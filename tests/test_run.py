"""
Unit tests for the main script
"""

import unittest
from run import main
from configparser import ConfigParser
from tests import check_config
import requests


class Test(unittest.TestCase):
    """Unit tests"""

    def read_text_in_file(self, path):
        """
        Read the text of a file
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def setUp(self):
        self.text = (
            "Inside the house the strong beam of the old man's "
            "torch flickers over dusty wooden paneling and a grandfather "
            "clock festooned with cobwebs.\nHe turns off his torch as he "
            "hears voices from an open doorway.\nThe snake appears and "
            "slithers through the doorway towards a figure hidden in an "
            "armchair."
        )

        # Load config file for tests
        unit_test_config_path, _ = check_config.check_config()
        self.config = ConfigParser()
        self.config.read(unit_test_config_path)

        # Load file tests
        self.file_present_fr = self.read_text_in_file(self.config.get("tests", "file_present_tense_fr"))
        self.file_present_en = self.read_text_in_file(self.config.get("tests", "file_present_tense_en"))
        self.text_cinema_fr = self.read_text_in_file(self.config.get("tests", "file_cinematographic_lexic_fr"))
        self.text_offensive_fr = self.read_text_in_file(self.config.get("tests", "file_offensive_fr"))
        self.text_duplication = self.read_text_in_file(self.config.get("tests", "file_duplication"))
        self.file_person_en = self.read_text_in_file(self.config.get("tests", "file_person_en"))
        self.file_person_fr = self.read_text_in_file(self.config.get("tests", "file_person_fr"))
        self.text_es = self.read_text_in_file(self.config.get("tests", "file_es"))
        self.file_person_en_tsv_correct = self.read_text_in_file(self.config.get("tests", "file_person_en_tsv_correct"))
        self.file_person_en_tsv_malformed = self.read_text_in_file(
            self.config.get("tests", "file_person_en_tsv_malformed"))
        self.file_coref_fr = self.read_text_in_file(self.config.get("tests", "file_coref_fr"))
        self.text_es = self.read_text_in_file(self.config.get("tests", "file_es"))
        self.file_emotion_fr = self.read_text_in_file(self.config.get("tests", "file_emotion_fr"))
        self.file_emotion_en = self.read_text_in_file(self.config.get("tests", "file_emotion_en"))

    def test_no_text(self):
        """
        Test with an empty text
        """
        with self.assertRaises(ValueError):
            # main("", "EN", 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)
            main("", 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)

    def test_unsupported_lang(self):
        """
        Test with an unsupported language
        """
        with self.assertRaises(ValueError):
            # main(self.text, "ES", 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)
            main(self.text_es, 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)

    def test_correct(self):
        """
        Test with correct input
        """
        # out = main(self.text, "EN", 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out = main(self.text, 15, 2, 2, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        self.assertTrue(out)
        self.assertEqual(len(out["documents"]), 3)

    def test_duplication(self):
        """
        Test for duplication
        """

        # out = main(self.text_duplication, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out = main(self.text_duplication, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        self.assertTrue(out)
        self.assertEqual(len(out["documents"][0]["features"]["duplication"][0]), 2)
        # TODO: check the presentation of the duplication in the output before the test

    def test_cinema(self):
        """
        Tests for cinematographic vocabulary
        """

        # out = main(self.text_cinema_fr, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out = main(self.text_cinema_fr, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        self.assertEqual(len(out["documents"][1]["features"]["cinema"]), 3)
        self.assertEqual(out["documents"][0]["features"]["cinema"][0]['token']['text'], 'Zoom')
        self.assertEqual(out["documents"][1]["features"]["cinema"][2]['token']['text'], 'actrices')

    def test_offensive(self):
        """
        Tests for offensive vocabulary
        """

        # out = main(self.text_cinema_fr, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out = main(self.text_offensive_fr, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        # self.assertEqual(out["documents"][1]["features"]["offensive"][0]['token']['text'], 'hystérique')
        self.assertEqual(out["documents"][1]["features"]["offensive"][0]['token']['text'], 'hystérique')
        self.assertEqual(out["documents"][2]["features"]["offensive"][0]['token']['text'], 'basanées')

    def test_present_tense(self):
        """
        Tests for present tense
        """

        # out_fr = main(self.file_present_fr, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        # out_en = main(self.file_present_en, "EN", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_fr = main(self.file_present_fr, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_en = main(self.file_present_en, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)

        self.assertEqual(len(out_fr["documents"][0]["features"]["tense_notpresent"]), 0)
        self.assertEqual(len(out_fr["documents"][1]["features"]["tense_notpresent"]), 0)
        self.assertEqual(out_fr["documents"][2]["features"]["tense_notpresent"][0]['token']['text'], 'jouaient')
        self.assertEqual(out_fr["documents"][3]["features"]["tense_notpresent"][0]['token']['text'], 'va')
        self.assertEqual(out_fr["documents"][4]["features"]["tense_notpresent"][2]['token']['text'], 'manger')

        self.assertEqual(out_en["documents"][0]["features"]["tense_notpresent"][0]['token']['text'], 'discovered')
        self.assertEqual(out_en["documents"][1]["features"]["tense_notpresent"][1]['token']['text'], 'been')
        self.assertEqual(len(out_en["documents"][2]["features"]["tense_notpresent"]), 0)
        self.assertEqual(len(out_en["documents"][3]["features"]["tense_notpresent"]), 0)
        self.assertEqual(out_en["documents"][4]["features"]["tense_notpresent"][0]['token']['text'], 'are')

    def test_person(self):
        """
        Test for detection of non-third person
        """
        # out_fr = main(self.file_person_fr, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        # out_en = main(self.file_person_en, "EN", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_fr = main(self.file_person_fr, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_en = main(self.file_person_en, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)

        self.assertEqual(out_fr["documents"][1]["features"]["person"][0]['token']['text'], 'Tu')
        self.assertEqual(len(out_fr["documents"][8]["features"]["person"]), 5)
        self.assertEqual(len(out_en["documents"][0]["features"]["person"]), 2)

    def test_format_tsv_correct(self):
        """
        Test for a text in well-formed TSV format
        """
        # out_en = main(self.file_person_en_tsv_correct, "EN", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_en = main(self.file_person_en_tsv_correct, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        self.assertEqual(len(out_en["documents"][0]["features"]["person"]), 2)

    def test_format_tsv_malformed(self):
        """
        Test for a text in malformed TSV format
        """
        with self.assertRaises(ValueError):
            # out_en = main(self.file_person_en_tsv_malformed, "EN", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
            out_en = main(self.file_person_en_tsv_malformed, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)

    def test_coref(self):
        """
        Test for coreference resolution
        """
        # out_fr = main(self.file_coref_fr, "FR", 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        out_fr = main(self.file_coref_fr, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, False)
        self.assertEqual(out_fr["documents"][0]["features"]["coref"][0]['token']['text'], 'Paul')
        # self.assertEqual(out_fr["documents"][1]["features"]["coref"][0]['token']['warning'], 0)
        # self.assertEqual(out_fr["documents"][2]["features"]["coref"][0]['token']['offset_start'], 81)
        # self.assertEqual(out_fr["documents"][2]["features"]["coref"][0]['token']['warning'], 1)
        # self.assertEqual(out_fr["documents"][2]["features"]["coref"][3]['token']['warning'], 1)

    def test_emotions(self):
        """
        Test for emotions detection
        We need to start the server first in order to test this feature
        """

        # test EN
        lines_en = self.file_emotion_en.split("\n")
        output_emotion = requests.post("http://localhost:5007/predict", json={'lines': lines_en}).json()

        self.assertEqual(output_emotion['0'][0]['token']['offset_end'], 22)
        self.assertEqual(output_emotion['0'][0]['token']['offset_start'], 13)
        self.assertEqual(output_emotion['0'][0]['token']['text'], 'merciless')
        self.assertEqual(output_emotion['0'][0]['token']['type'], 'state')
        self.assertEqual(output_emotion['0'][0]['token']['warning'], 1)

        # test FR
        lines_fr = self.file_emotion_fr.split("\n")
        output_emotion = requests.post("http://localhost:5007/predict", json={'lines': lines_fr}).json()

        self.assertEqual(output_emotion['0'][0]['token']['text'], 'est maussade.')
        self.assertEqual(output_emotion['0'][6]['token']['type'], 'action')
        self.assertEqual(output_emotion['0'][3]['token']['offset_end'], 42)

    def test_full(self):
        out_en = main(self.file_person_en, 15, 2, 5, ["VERB", "ADJ", "ADV"], True, True, 3, True)
        print(out_en)
