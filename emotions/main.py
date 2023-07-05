import json
import shutil
import time
from os import remove
from pathlib import Path
from typing import List, Tuple, Optional
from pydantic import BaseModel

from data_utils import (
    LabelEnum,
    SplitEnum,
    Sentence,
    SentimentTriple,
    Data,
)

class SpanModelDocument(BaseModel):
    sentences: List[List[str]]
    ner: List[List[Tuple[int, int, str]]]
    relations: List[List[Tuple[int, int, int, int, str]]]
    doc_key: str

    @property
    def is_valid(self) -> bool:
        return len(set(map(len, [self.sentences, self.ner, self.relations]))) == 1

    @classmethod
    def from_sentence(cls, x: Sentence):
        ner: List[Tuple[int, int, str]] = []
        for t in x.triples:
            ner.append((t.o_start, t.o_end, LabelEnum.opinion))
            ner.append((t.t_start, t.t_end, LabelEnum.target))
        ner = sorted(set(ner), key=lambda n: n[0])
        relations = [
            (t.o_start, t.o_end, t.t_start, t.t_end, t.label) for t in x.triples
        ]
        return cls(
            sentences=[x.tokens],
            ner=[ner],
            relations=[relations],
            doc_key=str(x.id),
        )

class SpanModelPrediction(SpanModelDocument):
    predicted_ner: List[List[Tuple[int, int, LabelEnum, float, float]]] = [
        []
    ]  # If loss_weights["ner"] == 0.0
    predicted_relations: List[List[Tuple[int, int, int, int, LabelEnum, float, float]]]

    def to_sentence(self) -> Sentence:
        for lst in [self.sentences, self.predicted_ner, self.predicted_relations]:
            assert len(lst) == 1

        triples = [
            SentimentTriple(o_start=os, o_end=oe, t_start=ts, t_end=te, label=label)
            for os, oe, ts, te, label, value, prob in self.predicted_relations[0]
        ]
        return Sentence(
            id=int(self.doc_key),
            tokens=self.sentences[0],
            pos=[],
            weight=1,
            is_labeled=False,
            triples=triples,
            spans=[lst[:3] for lst in self.predicted_ner[0]],
        )

class SpanModelData(BaseModel):
    root: Path
    data_split: SplitEnum
    documents: Optional[List[SpanModelDocument]]

    @classmethod
    def read(cls, path: Path) -> List[SpanModelDocument]:
        docs = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                raw: dict = json.loads(line)
                docs.append(SpanModelDocument(**raw))
        return docs

    def dump(self, path: Path, sep="\n"):
        for d in self.documents:
            assert d.is_valid
        print("-" * 50)
        print(path)
        with open(path, "w") as f:
            f.write(sep.join([d.json() for d in self.documents]))
        assert all(
            [a.dict() == b.dict() for a, b in zip(self.documents, self.read(path))]
        )

    @classmethod
    def from_data(cls, x: Data):
        data = cls(root=x.root, data_split=x.data_split)
        data.documents = [SpanModelDocument.from_sentence(s) for s in x.sentences]
        return data
