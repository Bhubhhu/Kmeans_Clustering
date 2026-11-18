"""Checks on the real data and on the clustering result. Run: python -m pytest tests -q"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import pipeline as p  # noqa: E402

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    df, info = p.run(RAW, str(out))
    return df, info, out


def test_real_data_is_loaded_and_clean(result):
    df, _, _ = result
    assert len(df) > 150
    assert df[p.FEATURES].notna().all().all()
    assert (df["population"] >= p.MIN_POPULATION).all()
    assert df[["dtp3_2019", "dtp3_2024"]].stack().between(0, 100).all()


def test_known_real_world_facts(result):
    df, _, _ = result
    by = df.set_index("country")
    assert by.loc["Sudan", "dtp3_net"] < -30          # Sudan's coverage collapsed after 2019
    assert by.loc["Finland", "archetype"] == p.STABLE  # a high-coverage country stays stable


def test_four_distinct_named_groups(result):
    df, _, _ = result
    assert set(df["archetype"]) == {p.STABLE, p.BACKSLIDE, p.LOW_UP, p.MID}
    assert df["archetype"].notna().all() and df["suggested_focus"].notna().all()


def test_group_names_match_their_numbers(result):
    df, _, _ = result
    g = df.groupby("archetype")
    assert g["dtp3_net"].mean().idxmin() == p.BACKSLIDE
    assert g["dtp3_2024"].mean().idxmax() == p.STABLE
    assert g["dtp3_2019"].mean().idxmin() == p.LOW_UP


def test_priority_score_and_outputs(result):
    df, info, out = result
    assert (df["priority_score"] >= 0).all()
    assert info["countries"] == len(df)
    for f in ["country_archetypes.csv", "timeseries.csv", "k_validation.csv", "method_comparison.csv",
              "archetype_summary.csv", "pca_loadings.csv", "summary.json"]:
        assert os.path.exists(os.path.join(str(out), f)), f


def test_result_is_reproducible(result):
    df, _, _ = result
    df2, _ = p.run(RAW, str(result[2]) + "_again")
    assert (df["cluster"] == df2["cluster"]).all()
