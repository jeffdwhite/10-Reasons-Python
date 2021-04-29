# %%
####################
# imports
####################
# standard library imports
from statistics import mean

# third party library imports
import pandas as pd
import numpy as np

# local library imports

# contstants
data_file = f"/Users/Jeff/Documents/indication_data.csv"
first_age_triange = 12
age_length_triangle = 12
triangle_type = "AY"
trend_factor = 0.015
permissible_loss_ratio = 0.55


# %%
####################
# helper functions
####################
# returns a list of tuples over which to perform ldf calculations
def create_period_list(first_age, age_length, periods):
    return [(first_age + (age_length * i), -i) for i in range(1, periods)]


# returns list of weighted average ldfs
def calculate_simple_average(df, first_age, age_length, periods):
    period_list = create_period_list(first_age, age_length, periods)
    return_list = [
        [
            round(df[str(items[0])].loc[i] / df[str(items[0] - age_length)].loc[i], 3)
            for i in range(periods + items[1])
        ]
        for items in period_list
    ]
    return return_list


# returns list of weighted average ldfs
def calculate_weighted_average(df, first_age, age_length, periods):
    period_list = create_period_list(first_age, age_length, periods)
    return_list = [
        round(
            sum(df[str(items[0])][: items[1]])
            / sum(df[str(items[0] - age_length)][: items[1]]),
            3,
        )
        for items in period_list
    ]
    return return_list


# %%
####################
# step 1 - read the data
####################
df_data = pd.read_csv(data_file).convert_dtypes()
df_data


####################
# step 2 - calculate LDFs
# 1. define functions
# 2. calculate paid ldfs
# 3. calculate case incurred ldfs
####################
# %%
# main calculation logic
def calculate_ldfs(df, first_age, age_length, data_type):
    # prepare dataframe
    df_type = (
        df.query(f"Type == '{data_type}'").drop(columns="Type").reset_index(drop=True)
    )

    # create averages
    paid_parameters = [
        df_type,
        first_age,
        age_length,
        len(df_type),
    ]
    ldfs_list = calculate_simple_average(*paid_parameters)
    simple_avg_list = [round(mean(x), 3) for x in ldfs_list]
    wtd_avg_list = calculate_weighted_average(*paid_parameters)

    # print section
    for age in ldfs_list:
        print(age)
    print(f"simple average {simple_avg_list}")
    print(f"weighted average {wtd_avg_list}")

    # output
    return [ldfs_list, simple_avg_list, wtd_avg_list]


# create cdf from ldf
def calculate_cdfs(selected_ldfs):
    reverse_ldfs = list(reversed([x for x in selected_ldfs]))
    start_value = 1
    return [round((start_value := start_value * i), 3) for i in reverse_ldfs]


# %%
####################
# 2. calculate paid ldfs
####################
paid_ldfs = calculate_ldfs(df_data, first_age_triange, age_length_triangle, "paid")
paid_selected_ldfs = [1.830, 1.440, 1.090, 1.020, 1.010, 1, 1.010, 1, 1, 1]
paid_selected_cdfs = calculate_cdfs(paid_selected_ldfs)

# %%
####################
# 3. calculate case incurred ldfs
####################
case_incurred_ldfs = calculate_ldfs(
    df_data, first_age_triange, age_length_triangle, "case_incurred"
)
case_incurred_selected_ldfs = [1.460, 1.270, 1.030, 1.020, 1, 1, 1, 1, 1, 1]
case_incurred_selected_cdfs = calculate_cdfs(case_incurred_selected_ldfs)


####################
# step 3 - Indication
# 1. selected ult
# 2. trended ult loss ratio
# 3. indication
####################
# %%
# 1. selected ult
# helper function
def get_latest_diagonal(df, index_column, data_type):
    df_type = (
        df.query(f"Type == '{data_type}'").drop(columns="Type").set_index(index_column)
    )
    columns_list = list(reversed(df_type.columns.tolist()))
    index_list = df_type.index.tolist()
    latest_diagonal_coordinates = tuple(zip(index_list, columns_list))
    return [
        df_type.at[coordinate[0], coordinate[1]]
        for coordinate in latest_diagonal_coordinates
    ]


df_indication = (
    df_data.query(f"Type == 'earned_premium'")
    .set_index(triangle_type)[["12"]]
    .rename(columns={"12": "earned_premium"})
)
df_indication = df_indication.assign(
    current_paid=get_latest_diagonal(df_data, triangle_type, "paid"),
    paid_cdf=paid_selected_cdfs,
    paid_ultimate=np.around(
        np.multiply(
            get_latest_diagonal(df_data, triangle_type, "paid"),
            paid_selected_cdfs,
        ),
        decimals=-1,
    ),
    current_case_incurred=get_latest_diagonal(df_data, triangle_type, "case_incurred"),
    case_incurred_cdf=case_incurred_selected_cdfs,
    case_incurred_ultimate=np.around(
        np.multiply(
            get_latest_diagonal(df_data, triangle_type, "case_incurred"),
            case_incurred_selected_cdfs,
        ),
        decimals=-1,
    ),
    selected_ultimate=0,
    net_trend=[
        round((1 + trend_factor) ** t, 3)
        for t in reversed(range(2, len(df_indication) + 2))
    ],
)
df_indication


# %%
# 2. trended ult loss ratio
df_indication["selected_ultimate"] = np.where(
    df_indication.index < 2017,
    df_indication["case_incurred_ultimate"],
    df_indication[["paid_ultimate", "case_incurred_ultimate"]].mean(axis=1),
)
df_indication["trended_ultimate_ratio"] = round(
    df_indication["selected_ultimate"]
    * df_indication["net_trend"]
    / df_indication["earned_premium"],
    3,
)
df_indication


# %%
# 3. indication
total_trended_ultimate_ratio = round(
    (df_indication["selected_ultimate"] * df_indication["net_trend"]).sum()
    / df_indication["earned_premium"].sum(),
    3,
)
indication = round(
    total_trended_ultimate_ratio / permissible_loss_ratio - 1, 3
)
print(f"selected trended ultimate ratio: {total_trended_ultimate_ratio}")
print(f"permissible loss ratio: {permissible_loss_ratio}")
print(f"indicated rate change need: {indication}")


# %%
