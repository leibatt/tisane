import tisane as ts 
from tisane.statistical_model import StatisticalModel
from tisane.smt.query_manager import QM
from tisane.smt.knowledge_base import KnowledgeBase
from tisane.smt.rules import *

import unittest 
from unittest.mock import patch
from unittest.mock import Mock
from z3 import *
from typing import Dict

# Declare data type
Object = DeclareSort('Object')

# Globals
iv = ts.Nominal('IV')
dv = ts.Numeric('DV')
fixed_effect = FixedEffect(iv.const, dv.const)
v1 = ts.Nominal('V1')
v2 = ts.Nominal('V2')
interaction = EmptySet(Object)
interaction = SetAdd(interaction, v1.const)
interaction = SetAdd(interaction, v2.const)
interaction_effect = Interaction(interaction)

class QueryManagerTest(unittest.TestCase): 

    def test_collect_rules_effects(self): 
        dv = ts.Nominal('DV')
        rules = QM.collect_rules(output='effects', dv_const=dv.const)
        
        kb = KnowledgeBase()
        kb.ground_effects_rules(dv_const=dv.const)

        self.assertIsInstance(rules, dict)
        self.assertTrue('effects_rules' in rules.keys())
        self.assertEquals(rules['effects_rules'], kb.effects_rules)
    
    def test_update_clauses(self): 
        global iv, dv, fixed_effect

        pushed_constraints=[NominalDataType(iv.const), NumericDataType(dv.const)]
        unsat_core=[fixed_effect, NoFixedEffect(iv.const, dv.const)]

        updated_constraints = QM.update_clauses(pushed_constraints=pushed_constraints, unsat_core=unsat_core, keep_clause=fixed_effect)
        self.assertEquals(len(updated_constraints), 3)
        self.assertTrue(fixed_effect in updated_constraints)
        self.assertTrue(NominalDataType(iv.const) in updated_constraints)
        self.assertTrue(NumericDataType(dv.const) in updated_constraints)

    def test_update_clauses_repeated_clauses(self): 
        global iv, dv, fixed_effect

        pushed_constraints=[fixed_effect, NominalDataType(iv.const), NumericDataType(dv.const)]
        unsat_core=[fixed_effect, NoFixedEffect(iv.const, dv.const)]

        updated_constraints = QM.update_clauses(pushed_constraints=pushed_constraints, unsat_core=unsat_core, keep_clause=fixed_effect)
        self.assertEquals(len(updated_constraints), 3)
        self.assertTrue(fixed_effect in updated_constraints)
        self.assertTrue(NominalDataType(iv.const) in updated_constraints)
        self.assertTrue(NumericDataType(dv.const) in updated_constraints)

    @patch('tisane.smt.input_interface.InputInterface.resolve_unsat', return_value=fixed_effect)
    def test_check_update_constraints(self, input): 
        global iv, dv, fixed_effect

        fixed_facts = list()
        fixed_facts.append(fixed_effect)
        fixed_facts.append(NoFixedEffect(iv.const, dv.const))
        
        s = Solver()
        kb = KnowledgeBase()
        kb.ground_effects_rules(dv_const=dv.const)
        s.add(kb.effects_rules)
        (solver, assertions) = QM.check_update_constraints(solver=s, assertions=fixed_facts)
        
        self.assertEquals(len(assertions), 1)
    
    @patch('tisane.smt.input_interface.InputInterface.resolve_unsat', return_value=fixed_effect)
    def test_postprocess_to_statistical_model(self, input): 
        global iv, dv, fixed_effect

        design = ts.Design(
            dv = dv, 
            ivs = ts.Level(identifier='id', measures=[iv])
        )

        fixed_facts = list()
        fixed_facts.append(fixed_effect)
        fixed_facts.append(NoFixedEffect(iv.const, dv.const))
        
        s = Solver()
        kb = KnowledgeBase()
        kb.ground_effects_rules(dv_const=dv.const)
        s.add(kb.effects_rules)
        (solver, assertions) = QM.check_update_constraints(solver=s, assertions=fixed_facts)
        
        model = solver.model()
        updated_facts = assertions
        graph = design.graph 
        statistical_model = StatisticalModel(dv=dv) 

        sm = QM.postprocess_to_statistical_model(model=model, facts=updated_facts, graph=graph, statistical_model=statistical_model)
        self.assertEquals(sm.dv, dv)
        self.assertTrue(iv in sm.fixed_ivs)
        self.assertEquals(sm.random_slopes, list())
        self.assertEquals(sm.random_intercepts, list())
        self.assertEquals(sm.interactions, list())
        self.assertIsNone(sm.family)
        self.assertIsNone(sm.link_func)

    @patch('tisane.smt.input_interface.InputInterface.resolve_unsat', return_value=interaction_effect)
    def test_postprocess_to_statistical_model(self, input): 
        global dv, v1, v2, interaction, interaction_effect

        design = ts.Design(
            dv = dv, 
            ivs = ts.Level(identifier='id', measures=[v1, v2])
        )

        facts = list()
        facts.append(FixedEffect(v1.const, dv.const))        
        facts.append(interaction_effect)
        facts.append(NoInteraction(interaction))

        s = Solver()
        kb = KnowledgeBase()
        kb.ground_effects_rules(dv_const=dv.const)
        s.add(kb.effects_rules)
        (solver, assertions) = QM.check_update_constraints(solver=s, assertions=facts)
        
        model = solver.model()
        updated_facts = assertions
        graph = design.graph 
        statistical_model = StatisticalModel(dv=dv) 
        
        sm = QM.postprocess_to_statistical_model(model=model, facts=updated_facts, graph=graph, statistical_model=statistical_model)
        self.assertEquals(sm.dv, dv)
        self.assertTrue(v1 in sm.fixed_ivs)
        self.assertFalse(v2 in sm.fixed_ivs)
        self.assertEquals(sm.random_slopes, list())
        self.assertEquals(sm.random_intercepts, list())
        self.assertEquals([(v1, v2)], sm.interactions)
        self.assertIsNone(sm.family)
        self.assertIsNone(sm.link_func)

