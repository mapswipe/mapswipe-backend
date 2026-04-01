import json
import typing
from pathlib import Path

import pandas as pd

from utils.geo.tile_functions import tile_coords_and_zoom_to_quad_key

CustomOptionType = list[dict[str, typing.Any]]  # TODO: fix typing

# TODO: use this https://strictly-typed-pandas.readthedocs.io/en/latest/#?


def _calc_count(df: pd.DataFrame) -> pd.Series:
    df_new = df.filter(like="count")
    return df_new.sum(axis=1)


def _calc_parent_option_count(
    df: pd.DataFrame,
    custom_options: dict[int, set[int]],
) -> pd.DataFrame:
    df_new = df.copy()
    # Update option count using sub options count
    for option, sub_options in custom_options.items():
        for sub_option in sub_options:
            df_new[f"{option}_count"] += df_new[f"{sub_option}_count"]
    return df_new


def _calc_share(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the share of each category on the total count."""
    share_df = df.filter(like="count").div(df.total_count, axis=0)
    share_df.drop("total_count", inplace=True, axis=1)
    share_df.columns = share_df.columns.str.replace("_count", "_share")
    return df.join(share_df)


def _add_missing_result_columns(
    df: pd.DataFrame,
    custom_options: dict[int, set[int]],
) -> pd.DataFrame:
    """Check if all possible answers columns are included in the grouped results
    data frame and add columns if missing.
    """
    all_custom_options_values_set = set(
        [_option for option, sub_options in custom_options.items() for _option in [option, *sub_options]],
    )
    return df.reindex(
        columns=sorted(all_custom_options_values_set),
        fill_value=0,
    )


def _calc_quadkey(row: pd.Series) -> str:
    """Calculate quadkey based on task id."""
    try:
        # TODO: This should come from task_specifics
        tile_z, tile_x, tile_y = row["task_id"].split("-")
        return tile_coords_and_zoom_to_quad_key(int(tile_x), int(tile_y), int(tile_z))
    except (ValueError, AttributeError):
        ...
    # return None if task_id is not composed of x,y ,z
    return ""  # XXX: This is None


def _calc_agreement(row: pd.Series) -> float:
    """For each task the "agreement" is computed (i.e. the extent to which
    raters agree for the i-th subject).

    This measure is a component of Fleiss' kappa: https://en.wikipedia.org/wiki/Fleiss%27_kappa
    """
    # Calculate total count as the sum of all categories
    n = row["total_count"]

    # TODO why are we dropping?
    row = row.drop(labels=["total_count"])
    # extent to which raters agree for the ith subject
    # set agreement to None if only one user contributed
    if n == 1 or n == 0:
        return float("nan")  # XXX: This is None
    return (sum([i**2 for i in row]) - n) / (n * (n - 1))


def _get_custom_options(custom_options: CustomOptionType):
    return {
        option["value"]: {sub_option["value"] for sub_option in option.get("subOptions", [])} for option in custom_options
    }


def _add_reference_to_agg_results(
    results_df: pd.DataFrame,
    agg_results_df: pd.DataFrame,
) -> pd.DataFrame:
    """Adds a 'reference' column to agg_results_df if it exists in results_df.
    For each task_id, all unique non-empty refs are collected into a list.
    If no refs exist for a task, the corresponding value is empty string.
    If results_df has no 'ref' column, agg_results_df is returned unchanged.
    """
    if "reference" not in results_df.columns:
        return agg_results_df

    refs_per_task = (
        results_df.groupby("task_id")["reference"]
        .apply(lambda x: list({r for r in x if pd.notna(r) and r not in ({}, "")}))
        .apply(lambda lst: json.dumps([json.loads(r) for r in lst]) if lst else "")
    )

    if refs_per_task.apply(lambda x: len(x) > 0).any():
        agg_results_df["reference"] = agg_results_df["task_id"].map(refs_per_task).fillna("")

    return agg_results_df


def generate_mapping_results_aggregate_by_task(
    *,
    destination_filename: Path,
    results_df: pd.DataFrame,
    tasks_df: pd.DataFrame,
    custom_options_raw: CustomOptionType,
):
    custom_options = _get_custom_options(custom_options_raw)

    # Group by project_id, group_id, task_id and use result's value as column with counts
    # Eg.
    # project_id, group_id, task_id, 0, 1, 2, 3
    # p-01      , g-01,   , t-01   , 0, 0, 1, 0
    results_by_task_id_df = results_df.groupby(["project_id", "group_id", "task_id", "result"]).size().unstack(fill_value=0)

    # Add missing columns to the dataframe, if 4 was missing from last df, then it will be added
    # Eg.
    # project_id, group_id, task_id, 0, 1, 2, 3, 4
    # p-01      , g-01,   , t-01   , 0, 0, 1, 0, 0
    results_by_task_id_df = _add_missing_result_columns(
        results_by_task_id_df,
        custom_options,
    )

    # Add _count to the values column
    # Eg.
    # project_id, group_id, task_id, count_0, count_1, count_2, count_3, count_4
    # p-01      , g-01,   , t-01   , 0      , 0      , 1      , 0      , 0
    results_by_task_id_df = results_by_task_id_df.add_suffix("_count")
    results_by_task_id_df["total_count"] = _calc_count(results_by_task_id_df)

    # This is for sub_options
    # When we have options as suboptions, we need to add the child count to the parent
    # Eg: if 0 includes 1 and 2 as child then we need to do this
    # results_by_task_id_df["0_count"] += results_by_task_id_df["1_count"] + results_by_task_id_df["2_count"]
    results_by_task_id_df = _calc_parent_option_count(
        results_by_task_id_df,
        custom_options,
    )

    # Calculate share per value - add new column share
    results_by_task_id_df = _calc_share(results_by_task_id_df)

    # Calculate agreement per value - add new column agreement
    results_by_task_id_df["agreement"] = results_by_task_id_df.filter(like="count").apply(
        _calc_agreement,
        axis=1,
    )

    # Calculate quadkey from task (TODO) - add new column quadkey
    results_by_task_id_df.reset_index(level=["task_id"], inplace=True)
    results_by_task_id_df["quadkey"] = results_by_task_id_df.apply(
        _calc_quadkey,
        axis=1,
    )

    # Make task df ready to be merge to results_by_task_id_df
    tasks_df = tasks_df.drop(columns=["project_id", "group_id"])

    # Merge the tasks and results_by_task_id_df df
    agg_results_df = results_by_task_id_df.merge(
        tasks_df,
        left_on="task_id",
        right_on="task_id",
    )

    agg_results_df = _add_reference_to_agg_results(results_df, agg_results_df)

    agg_results_df.to_csv(destination_filename, index_label="idx")

    return agg_results_df
