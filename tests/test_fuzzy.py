import unittest
import sys
import os

sys.path.append(os.getcwd())
from src import voice

class TestFuzzyMatching(unittest.TestCase):
    def test_normalize(self):
        ctx = {
            'A': 'Stratosphere',
            'B': 'Mesosphere',
            'C': 'Ionosphere',
            'D': 'Troposphere'
        }
        
        # Direct matches
        self.assertEqual(voice.normalize_answer("A"), 'A')
        self.assertEqual(voice.normalize_answer("Option B"), 'B')
        
        # Fuzzy Content matches
        self.assertEqual(voice.normalize_answer("Stratosphere", ctx), 'A')
        self.assertEqual(voice.normalize_answer("Meso sphere", ctx), 'B') # space error
        self.assertEqual(voice.normalize_answer("Ionosphere layer", ctx), 'C') # substring/extra
        
        # Close enough? "Troposhere" (typo)
        self.assertEqual(voice.normalize_answer("Troposhere", ctx), 'D')
        
        # No match
        self.assertIsNone(voice.normalize_answer("Jupiter", ctx))

if __name__ == '__main__':
    unittest.main()
