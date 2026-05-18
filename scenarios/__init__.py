from scenarios.q_series import Q_SERIES
from scenarios.t_series import T_SERIES
from scenarios.c_series import C_SERIES
from scenarios.l_series import L_SERIES
from scenarios.m_series import M_SERIES
from scenarios.f_series import F_SERIES
from abs.scenario import Scenario

ALL_SCENARIOS: list[Scenario] = Q_SERIES + T_SERIES + C_SERIES + L_SERIES + M_SERIES

SERIES_MAP: dict[str, list[Scenario]] = {
    "Q": Q_SERIES,
    "T": T_SERIES,
    "C": C_SERIES,
    "L": L_SERIES,
    "M": M_SERIES,
    "F": F_SERIES,
}
