import ast
import copy
import json
import os
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel

RawTriple = Tuple[List[int], int, int, int, int]
Span = Tuple[int, int]

class SplitEnum(str, Enum):
    train = "train"
    dev = "dev"
    test = "test"

class LabelEnum(str, Enum):
    positive = "POS"
    negative = "NEG"
    neutral = "NEU"
    opinion = "OPINION"
    target = "TARGET"

    @classmethod
    def as_list(cls):
        return [cls.neutral, cls.positive, cls.negative]

    @classmethod
    def i_to_label(cls, i: int):
        return cls.as_list()[i]

    @classmethod
    def label_to_i(cls, label) -> int:
        return cls.as_list().index(label)

class SentimentTriple(BaseModel):
    o_start: int
    o_end: int
    t_start: int
    t_end: int
    label: LabelEnum

    @classmethod
    def make_dummy(cls):
        return cls(o_start=0, o_end=0, t_start=0, t_end=0, label=LabelEnum.neutral)

    @property
    def opinion(self) -> Tuple[int, int]:
        return self.o_start, self.o_end

    @property
    def target(self) -> Tuple[int, int]:
        return self.t_start, self.t_end

class TagMaker(BaseModel):
    @staticmethod
    def run(spans: List[Span], labels: List[LabelEnum], num_tokens: int) -> List[str]:
        raise NotImplementedError

class BioesTagMaker(TagMaker):
    @staticmethod
    def run(spans: List[Span], labels: List[LabelEnum], num_tokens: int) -> List[str]:
        tags = ["O"] * num_tokens
        for (start, end), lab in zip(spans, labels):
            assert end >= start
            length = end - start + 1
            if length == 1:
                tags[start] = f"S-{lab}"
            else:
                tags[start] = f"B-{lab}"
                tags[end] = f"E-{lab}"
                for i in range(start + 1, end):
                    tags[i] = f"I-{lab}"
        return tags

class Sentence(BaseModel):
    tokens: List[str]
    pos: List[str]
    weight: int
    id: int
    is_labeled: bool
    triples: List[SentimentTriple]
    spans: List[Tuple[int, int, LabelEnum]] = []
    
    @classmethod
    def from_line_format(cls, text: str):
        front, back = text.split("#### #### ####")
        tokens = front.split(" ")
        triples = []

        for a, b, label in ast.literal_eval(back):
            t = SentimentTriple(
                t_start=a[0],
                t_end=a[0] if len(a) == 1 else a[-1],
                o_start=b[0],
                o_end=b[0] if len(b) == 1 else b[-1],
                label=label,
            )
            triples.append(t)

        return cls(
            tokens=tokens, triples=triples, id=0, pos=[], weight=1, is_labeled=True
        )

    def to_line_format(self) -> str:
        # ([1], [4], 'POS')
        # ([1,2], [4], 'POS')
        triplets = []
        for t in self.triples:
            parts = []
            for start, end in [(t.t_start, t.t_end), (t.o_start, t.o_end)]:
                if start == end:
                    parts.append([start])
                else:
                    parts.append([start, end])
            parts.append(f"{t.label}")
            triplets.append(tuple(parts))

        line = " ".join(self.tokens) + "#### #### ####" + str(triplets) + "\n"
        assert self.from_line_format(line).tokens == self.tokens
        assert self.from_line_format(line).triples == self.triples
        return line

class Data(BaseModel):
    root: Path
    data_split: SplitEnum
    sentences: Optional[List[Sentence]]
    full_path: str = ""
    num_instances: int = -1
    opinion_offset: int = 3  # Refer: jet_o.py
    is_labeled: bool = False

    def load(self):
        if self.sentences is None:
            path = self.root / f"{self.data_split}.txt"
            if self.full_path:
                path = self.full_path

            print("+" * 50)            
            print(self.root)
            print(self.data_split)
            print(path)
            with open(path) as f:
                self.sentences = [Sentence.from_line_format(line) for line in f]

    @classmethod
    def load_from_full_path(cls, path: str):
        data = cls(full_path=path, root=Path(path).parent, data_split=SplitEnum.train)
        data.load()
        return data

    def save_to_path(self, path: str):
        assert self.sentences is not None
        Path(path).parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w") as f:
            for s in self.sentences:
                f.write(s.to_line_format())

        data = Data.load_from_full_path(path)
        assert data.sentences is not None
        for i, s in enumerate(data.sentences):
            assert s.tokens == self.sentences[i].tokens
            assert s.triples == self.sentences[i].triples
