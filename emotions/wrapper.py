import json
import sys
import os
import ast
import torch
from pathlib import Path
from typing import List
from allennlp.commands.train import train_model
from allennlp.common import Params
from pydantic import BaseModel

# Make sure the path to the emotions folder is in the sys path
sys.path.append(str(Path(__file__).parent))

from data_utils import Data, Sentence, SplitEnum, SentimentTriple
from main import SpanModelData, SpanModelPrediction
from utils import Shell

class SpanModel(BaseModel):
    save_dir: str
    random_seed: int

    def save_temp_data(self, sentences: List[str], name: str) -> Path:
        path_temp = Path(self.save_dir) / "temp_data" / f"{name}.json"
        path_temp = path_temp.resolve()
        path_temp.parent.mkdir(exist_ok=True, parents=True)

        data = Data(
            root=Path(),
            data_split=SplitEnum.test,
            sentences=[Sentence.from_line_format(sent.strip() + "#### #### ####[]") for sent in sentences],
        )

        assert data.sentences is not None
        for s in data.sentences:
            s.triples = [SentimentTriple.make_dummy()]

        span_data = SpanModelData.from_data(data)
        span_data.dump(path_temp)
        return path_temp

    def get_line_output(self, line_pred):        
        line_output = []
        line, pred_triplets_str = line_pred.to_sentence().to_line_format().strip().split("#### #### ####")
        pred_triplets = ast.literal_eval(pred_triplets_str)

        if pred_triplets:
            for triplet in pred_triplets:
                # Sentiment triplets are of the format: (target tokens, emotion tokens and polarity)
                # In our use case, polarity in triplets represents the type of emotions:
                # POS = "state" and NEG = "action"
                _, emotion_tokens, polarity = triplet

                # Predictions with a NEU polarity (a polarity that was not determined) are ignored
                if polarity != "NEU":

                    # Here we need to go from token indices (as included in predictions by Span-ASTE) to 
                    # char indices within each line
                    tokens = line.split()
                    # Token indices
                    if len(emotion_tokens) == 2:
                        token_idx_beg, token_idx_end = emotion_tokens
                    else:
                        token_idx_beg = emotion_tokens[0]
                        token_idx_end = emotion_tokens[0]
                    # Char indices within each line
                    char_span_beg = 0
                    char_span_end = 0
                    # Used to keep track of the current char in the string we'll be looping through
                    curr_num_char = 0
                    # Loop string and count chars       
                    for i, token in enumerate(tokens):
                        if i == token_idx_beg:
                            char_span_beg = curr_num_char
                            if token_idx_beg == token_idx_end:
                                char_span_end = curr_num_char + len(token)
                                break
                        elif i == token_idx_end:
                            char_span_end = curr_num_char + len(token)
                            break
                        # Update counter
                        curr_num_char += len(token) + 1

                    line_output.append(
                        {
                            "token": {
                                "text"          : line[char_span_beg:char_span_end],
                                "offset_start"  : char_span_beg,
                                "offset_end"    : char_span_end,
                                "type"          : "state" if polarity == "POS" else "action",
                                "warning"       : 1 if polarity == "POS" else 0,
                            }
                        }
                    )
        return line_output

    def predict(self, sentences:List[str]):             
        work_dir = str(Path(__file__).parent)
        path_model = Path(self.save_dir) / "weights" / "model.tar.gz"
        path_temp_in = self.save_temp_data(sentences, "pred_in")
        path_temp_out = Path(self.save_dir) / "temp_data" / "pred_out.json"
        if path_temp_out.exists():
            os.remove(path_temp_out)

        shell = Shell()
        shell.run(
            f"cd {work_dir} && allennlp predict {path_model}",
            str(path_temp_in),
            predictor="span_model",
            include_package="span_model",
            use_dataset_reader="",
            output_file=str(path_temp_out),
            # force disabled CUDA (even if available)
            cuda_device="-1" if torch.cuda.is_available() else "-1",
            silent="",
        )

        # Transform predictions into JSON document
        main_output = {}
        with open(path_temp_out) as f:
            line_preds = [SpanModelPrediction(**json.loads(line.strip())) for line in f]
            for i, line_pred in enumerate(line_preds):                
                line_output = self.get_line_output(line_pred)
                main_output[i] = line_output
                        
        return main_output
