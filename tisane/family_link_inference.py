"""
Inferring candidnate statistical models from the IR (model effects structures) and DV (family and link functions)
"""

from abc import abstractmethod
from tisane.family import (
    AbstractFamily,
    AbstractLink,
    BinomialFamily,
    GammaFamily,
    GaussianFamily,
    IdentityLink,
    InverseGaussianFamily,
    MultinomialFamily,
    NegativeBinomialFamily,
    PoissonFamily,
    TweedieFamily,
    IdentityLink,
    InverseLink,
    InverseSquaredLink,
    LogLink,
    LogitLink,
    ProbitLink,
    CLogLogLink,
    PowerLink,
    OPowerLink,
    NegativeBinomialLink,
    LogLogLink,
)
from tisane import variable
from tisane.variable import (
    AbstractVariable,
    Numeric,
    Nominal,
    Ordinal,
    Has,
    Moderates,
    NumberValue,
)
from tisane.random_effects import RandomSlope, RandomIntercept
from tisane.graph import Graph
from tisane.design import Design
from itertools import chain, combinations
from typing import Dict, List, Set, Any, Tuple
import typing  # for Union

# Family functions are members of the exponential family of probability distributions that are widely used and implemented in statsmodels, the target backend for code generation
# https://www.statsmodels.org/stable/generated/statsmodels.genmod.generalized_linear_model.GLM.html#statsmodels.genmod.generalized_linear_model.GLM
def infer_family_functions(query: Design) -> Set[AbstractFamily]:
    family_candidates = set()

    dv = query.dv
    if isinstance(dv, Numeric):
        family_candidates.add(GaussianFamily(dv))
        family_candidates.add(InverseGaussianFamily(dv))
        family_candidates.add(GammaFamily(dv))
        family_candidates.add(TweedieFamily(dv))
        family_candidates.add(PoissonFamily(dv))
    elif isinstance(dv, Ordinal):
        # Treats ordinal data as continuous
        family_candidates.add(GaussianFamily(dv))
        family_candidates.add(InverseGaussianFamily(dv))
        family_candidates.add(GammaFamily(dv))
        family_candidates.add(TweedieFamily(dv))
        family_candidates.add(PoissonFamily(dv))
        # Treats ordinal data as discrete
        family_candidates.add(BinomialFamily(dv))
        family_candidates.add(NegativeBinomialFamily(dv))
        family_candidates.add(MultinomialFamily(dv))
    else:
        assert isinstance(dv, Nominal)

        if dv.get_cardinality() == 2:
            family_candidates.add(BinomialFamily(dv))
        else:
            assert dv.get_cardinality() > 2
            family_candidates.add(NegativeBinomialFamily(dv))
            family_candidates.add(MultinomialFamily(dv))

    return family_candidates


def infer_link_functions(query: Design, family: AbstractFamily):
    link_candidates = set()

    # TODO: Identify which of these is actually implemented in Statsmodels
    dv = query.dv
    if isinstance(family, GaussianFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(LogitLink(dv))
        link_candidates.add(ProbitLink(dv))
        link_candidates.add(CLogLogLink(dv))
        link_candidates.add(PowerLink(dv))
        link_candidates.add(OPowerLink(dv))
        link_candidates.add(NegativeBinomialLink(dv))
        link_candidates.add(LogLogLink(dv))
    elif isinstance(family, InverseGaussianFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(PowerLink(dv))
    elif isinstance(family, GammaFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(PowerLink(dv))
    elif isinstance(family, TweedieFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(PowerLink(dv))
    elif isinstance(family, PoissonFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(PowerLink(dv))
    elif isinstance(family, BinomialFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(LogitLink(dv))
        link_candidates.add(ProbitLink(dv))
        link_candidates.add(CLogLogLink(dv))
        link_candidates.add(PowerLink(dv))
        link_candidates.add(OPowerLink(dv))
        link_candidates.add(LogLogLink(dv))
        # link_candidates.add(LogCLink(dv))
    elif isinstance(family, NegativeBinomialFamily):
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(PowerLink(dv))
        link_candidates.add(NegativeBinomialLink(dv))
    else:
        assert isinstance(family, MultinomialFamily)
        link_candidates.add(IdentityLink(dv))
        link_candidates.add(LogLink(dv))
        link_candidates.add(LogitLink(dv))
        link_candidates.add(ProbitLink(dv))

    return link_candidates