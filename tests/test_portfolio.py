import ast
import copy
import hashlib
import json
from pathlib import Path
import time
import unittest
import SeanGilbert as player
from evaluation.summarize import summarize
from player_versions.verified_denial_08.GameCore import Position, generate, decode, encode, from_state, terminal_diff
from player_versions.verified_denial_08.SelectiveEndgamePlayer import ProofCache, proof_key, OutcomeSolver

ROOT=Path(__file__).resolve().parents[1]

class FrozenPackageTests(unittest.TestCase):
    def test_runtime_identity(self):
        manifest=json.loads((ROOT/'evidence/frozen_manifest.json').read_text())
        standalone=(ROOT/'SeanGilbert.py').read_bytes()
        self.assertEqual(hashlib.sha256(standalone).hexdigest(),manifest['player_sha256'])
        sources=next(ast.literal_eval(n.value) for n in ast.parse(standalone).body
                     if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_SOURCES' for t in n.targets))
        self.assertEqual(len(sources),19)
        for name, text in sources:
            self.assertEqual((ROOT/'player_versions/verified_denial_08'/name).read_text(),text)
        for name, expected in manifest['frozen_runtime_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'player_versions/verified_denial_08'/name).read_bytes()).hexdigest(),expected)

    def test_public_fallback_preserves_saved_inputs_and_returns_legal_move(self):
        cases=json.loads((ROOT/'examples/saved_states.json').read_text())
        for case in cases:
            with self.subTest(case=case['id']):
                state=copy.deepcopy(case['state']); before=copy.deepcopy(state)
                player.configure(seconds=0)
                move=player.getMove(state)
                self.assertEqual(state,before)
                self.assertIn(encode(move),{e.move for e in generate(from_state(state))})
                self.assertEqual(set(move),{'Row','Col','Direction'})
        self.assertEqual(player.name(),'Sean Gilbert')

    def test_terminal_contract(self):
        player.configure(seconds=0)
        with self.assertRaisesRegex(ValueError,'terminal'):
            player.getMove({'Board':[0]*36,'Turn':'Dark','LightCapture':18,'DarkCapture':18})

class RuleEdgeCaseTests(unittest.TestCase):
    def east_capture(self, stacks):
        board=[0]*36
        for index,value in stacks.items(): board[index]=value
        return next(e for e in generate(Position(tuple(board),1,0)) if decode(e.move)=={'Row':0,'Col':1,'Direction':'E'})

    def test_empty_enemy_grows_and_positive_smaller_enemy_is_captured(self):
        edge=self.east_capture({1:3,3:1,4:1})
        self.assertEqual(edge.gain,2)
        self.assertEqual(edge.child.board[:6],(0,0,1,2,0,0))
        self.assertEqual(edge.child.diff,2)

    def test_equal_enemy_not_captured_and_threshold_stays_original_size(self):
        edge=self.east_capture({1:3,2:3,4:2})
        self.assertEqual(edge.gain,3)
        self.assertEqual(edge.child.board[:6],(0,0,4,1,0,0))

    def test_edge_returns_unspent_stones_to_source(self):
        board=[0]*36; board[3]=4; board[4]=1
        edge=next(e for e in generate(Position(tuple(board),1,0)) if decode(e.move)=={'Row':0,'Col':3,'Direction':'E'})
        self.assertEqual(edge.child.board[3],2)
        self.assertEqual(edge.gain,2)

    def test_terminal_bonus_belongs_to_previous_mover(self):
        board=[0]*36; board[1]=3
        pos=Position(tuple(board),-1,-3)
        self.assertEqual(generate(pos),[])
        self.assertEqual(terminal_diff(pos),0)
        won,_=OutcomeSolver(ProofCache()).solve(pos,time.perf_counter()+1)
        self.assertFalse(won)  # Dark to move loses the tied final score.

class ProofCacheTests(unittest.TestCase):
    def test_capture_difference_is_part_of_proof_key(self):
        pos=Position((0,)*36,1,0)
        self.assertNotEqual(proof_key(pos),proof_key(pos._replace(diff=1)))

    def test_conflicting_proof_is_rejected(self):
        cache=ProofCache(4); cache.put(b'a',True,None)
        with self.assertRaises(AssertionError): cache.put(b'a',False,None)

    def test_cache_retains_bounded_generations(self):
        cache=ProofCache(4)
        for index in range(9):
            cache.put(bytes([index]),True,None)
            self.assertLessEqual(len(cache),4)
        self.assertIsNone(cache.get(bytes([0])))
        self.assertIsNotNone(cache.get(bytes([8])))

class HistoricalDataTests(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'evidence/selection_games.json').read_text())

    def test_recorded_totals_and_color_balance(self):
        result=summarize(self.rows)
        self.assertEqual((result['games'],result['wins'],result['losses'],result['boards']),(22,14,8,7))
        self.assertEqual(result['colors'],{'Dark':{'wins':7,'losses':4},'Light':{'wins':7,'losses':4}})
        self.assertEqual(result['stages']['random_extension'],{'wins':6,'losses':2})

    def test_duplicate_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'): summarize(self.rows+[self.rows[0]])

    def test_winner_must_match_scores(self):
        self.rows[0]['winner']='invalid'
        with self.assertRaisesRegex(ValueError,'Winner'): summarize(self.rows)

    def test_missing_color_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'pair'): summarize(self.rows[1:])

    def test_blank_and_negative_data_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'No historical'): summarize([])
        self.rows[0]['scores']['Light']=-1
        with self.assertRaisesRegex(ValueError,'Scores'): summarize(self.rows)

if __name__=='__main__': unittest.main()
