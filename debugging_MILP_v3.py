# %%
from fjss import FJSS2, FJSS3, FJSS4
import numpy as np
import time

from itertools import product
from collections import OrderedDict

from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from utils import *  # get_m_value, parse_data
import pandas as pd
from checking_constraints import check_constraints_milp, check_constraints_cp

# %%

print("setting up initial parameters")

infinity = 1.0e7

n_opt_selected = 35


# %%
# def single_run(n_opt_selected=10, method="CP"):
#     # load the data
#     (
#         n_opt,
#         n_mach,
#         operation_data,
#         machine_data,
#         para_lmin,
#         para_lmax,
#         para_p,
#         para_h,
#         para_w,
#         para_delta,
#         para_a,
#         para_mach_capacity,
#         big_m,
#     ) = load_data()

#     n_opt = n_opt_selected

#     para_p_horizon = np.copy(para_p[:n_opt_selected, :])
#     para_p_horizon[para_p_horizon == np.inf] = 0

#     # para_h = np.empty((n_opt, n_mach), dtype=object)
#     para_h_horizon = np.copy(para_h[:n_opt_selected, :])
#     para_h_horizon[para_h_horizon == np.inf] = 0

#     para_lmax_horizon = np.copy(para_lmax[:n_opt_selected, :n_opt_selected])
#     para_lmax_horizon[para_lmax_horizon == np.inf] = 0

#     horizon = (
#         np.sum(para_p_horizon, axis=1)
#         + np.sum(para_h_horizon, axis=1)
#         + np.sum(para_lmax_horizon, axis=1)
#     )
#     horizon = int(np.sum(horizon)) + 1

#     para_lmin[para_lmin == -np.inf] = -infinity
#     para_lmin[para_lmin == np.inf] = infinity
#     para_lmax[para_lmax == np.inf] = infinity
#     para_lmax[para_lmax == -np.inf] = -infinity

#     para_p[para_p == np.inf] = infinity
#     para_p[para_p == -np.inf] = -infinity
#     para_w[para_w == np.inf] = infinity
#     para_w[para_w == -np.inf] = -infinity

#     para_a[para_a == np.inf] = infinity
#     para_a[para_a == -np.inf] = -infinity

#     # =====================================================
#     # convert all the numpy arrays with integers data type
#     para_lmin = para_lmin.astype(int)
#     para_lmax = para_lmax.astype(int)
#     para_p = para_p.astype(int)
#     para_w = para_w.astype(int)
#     para_a = para_a.astype(int)
#     para_delta = para_delta.astype(int)
#     para_mach_capacity = para_mach_capacity.astype(int)

#     para_lmin = para_lmin[:n_opt_selected, :n_opt_selected]
#     para_lmax = para_lmax[:n_opt_selected, :n_opt_selected]

#     para_p = para_p[:n_opt_selected, :]
#     para_h = para_h[:n_opt_selected, :]
#     para_w = para_w[:n_opt_selected, :]

#     para_a = para_a[:n_opt_selected, :n_opt_selected, :]

#     # machines
#     machines = [str(i) for i in range(6)]
#     # operations
#     operations = [str(i) for i in range(n_opt_selected)]

#     operations = operations[:n_opt_selected]
#     machines = machines[:n_mach]

#     # =====================================================
#     if method == "CP":
#         # time the running time for the CP model
#         start_time = time.time()
#         fjss2 = FJSS2(
#             operations=operations,
#             machines=machines,
#             para_p=para_p,
#             para_a=para_a,
#             para_w=para_w,
#             para_h=para_h,
#             para_delta=para_delta,
#             para_mach_capacity=para_mach_capacity,
#             para_lmin=para_lmin,
#             para_lmax=para_lmax,
#             precedence=None,
#             model_string=None,
#             inf_cp=1.0e6,
#             num_workers=4,
#             verbose=True,
#         )
#         fjss2.build_model_ortools()
#         fjss2.solve_ortools()
#         # get the running time in seconds
#         running_time = time.time() - start_time

#         new_row = {
#             "method": method,
#             "n_opt": n_opt_selected,
#             "n_mach": n_mach,
#             "running_time_seconds": running_time,
#             "num_constraints": 0,
#             "makespan": fjss2.var_c_max,
#         }
#     elif method == "MILP":
#         para_a = np.einsum("mij->ijm", para_a)
#         # time the running time for the MILP model
#         start_time = time.time()
#         fjss3 = FJSS3(
#             operations=operations,
#             machines=machines,
#             para_p=para_p,
#             para_a=para_a,
#             para_w=para_w,
#             para_h=para_h,
#             para_delta=para_delta,
#             para_mach_capacity=para_mach_capacity,
#             para_lmin=para_lmin,
#             para_lmax=para_lmax,
#             precedence=None,
#             model_string=None,
#             inf_milp=1.0e7,
#             num_workers=4,
#             verbose=True,
#         )
#         fjss3.solve_gurobi()
#         running_time = time.time() - start_time
#         new_row = {
#             "method": method,
#             "n_opt": n_opt_selected,
#             "n_mach": n_mach,
#             "running_time_seconds": running_time,
#             "num_constraints": fjss3.solver.NumConstraints(),
#             "makespan": fjss3.var_c_max,
#         }
#     else:
#         raise ValueError("Invalid method!")

#     return new_row


def load_data():
    n_opt, n_mach, operation_data, machine_data = parse_data("gfjsp_10_5_1.txt")
    operation_data["0"]["h"] = 0
    operation_data["1"]["h"] = 0
    operation_data["2"]["h"] = 0
    operation_data["3"]["h"] = 20

    # define the parameters

    # minimum lag between the starting time of operation i and the ending time of operation j
    para_lmin = np.full((n_opt, n_opt), dtype=object, fill_value=-np.inf)
    # maximum lag between the starting time of operation i and the ending time of operation j
    para_lmax = np.full((n_opt, n_opt), dtype=object, fill_value=np.inf)

    # processing time of operation i in machine m
    # para_p = np.full((n_opt, n_mach), dtype=object, fill_value=np.inf)
    para_p = np.full((n_mach, n_opt), dtype=object, fill_value=np.inf)

    # the shape of h in the original file is (n_machine) while the shape of para_h in the
    # paper is (n_opt, n_mach)
    # maximum holding time of operation i in machine m
    para_h = np.empty((n_opt, n_mach), dtype=object)
    # para_h = np.empty(n_mach, dtype=object)

    # mapping of operation i to machine m
    # 20 for the furnaces, 0 for Cutting, Pressing, and Forging
    # 0: Cutting; 1: Pressing; 2: Forging; 3: Furnace
    holding_time_dict = {
        "0": 0,
        "1": 0,
        "2": 0,
        "3": 20,
    }

    # weight of operation i in machine m
    # para_w = np.empty((n_opt, n_mach), dtype=object)
    # para_w = np.full((n_mach, n_opt), dtype=object, fill_value=np.inf)
    para_w = np.full((n_mach, n_opt), dtype=object, fill_value=0)

    # input/output delay time between two consecutive operations in mahcine m
    # para_delta = np.empty((n_mach), dtype=object)
    para_delta = np.full((n_mach), dtype=object, fill_value=0)

    # setup time of machine m when processing operation i before j
    # para_a = np.full((n_opt, n_opt, n_mach), dtype=object, fill_value=np.inf)
    para_a = np.full((n_mach, n_opt, n_opt), dtype=object, fill_value=-np.inf)

    # capacity of machine
    # para_mach_capacity = np.empty((n_mach), dtype=object)
    para_mach_capacity = np.full((n_mach), dtype=object, fill_value=0)
    for m in range(n_mach):
        # capacity of machine is a set of constant numbers
        para_mach_capacity[m] = machine_data[str(m)]["c"]

        # input/output delay time between two consecutive operations in mahcine m
        # delta(m): loading and unloading time of machine m (=1 for all machines)
        para_delta[m] = 1

        # set up time of machine m when processing operation i before j
        # a(i,j,m): setup time of machine m when processing operation i before j (aijm = -inf if there
        # is no setups)
        for idx_setup, setup_data in enumerate(machine_data[str(m)]["setup_data"][0]):
            para_a[m, int(setup_data[0]), int(setup_data[1])] = setup_data[2]

        # maximum holding time of operation i in machine m
        para_h[:, m] = holding_time_dict[str(machine_data[str(m)]["t"])]

    # lag time
    for i in range(n_opt):
        for idx_lag, lag_data in enumerate(operation_data[str(i)]["lag"]):
            # minimum lag between the starting time of operation i and the ending time of operation j
            para_lmin[i, int(lag_data[0])] = lag_data[1]
            # maximum lag between the starting time of operation i and the ending time of operation j
            para_lmax[i, int(lag_data[0])] = lag_data[2]

        for idx_pw, pw_data in enumerate(operation_data[str(i)]["pw"]):
            # operation_data[str(1)]["pw"]
            # # the shape of para_p in the original file is the transpose of the shape of para_p
            # para_p[i, int(pw_data[0])] = pw_data[1]
            # # the shape of para_w in the original file is the transpose of the shape of para_w
            # para_w[i, int(pw_data[0])] = pw_data[2]

            # the shape of para_p in the original file is the transpose of the shape of para_p
            para_p[int(pw_data[0]), i] = pw_data[1]
            # the shape of para_w in the original file is the transpose of the shape of para_w
            para_w[int(pw_data[0]), i] = pw_data[2]

    # reformat the shape of para_p and para_w
    para_p = para_p.T
    para_w = para_w.T

    # # reshape the shape of para_a
    # para_a = np.einsum("mij->ijm", para_a)

    return (
        n_opt,
        n_mach,
        operation_data,
        machine_data,
        para_lmin,
        para_lmax,
        para_p,
        para_h,
        para_w,
        para_delta,
        para_a,
        para_mach_capacity,
    )


# %%
print("load and setup data")

(
    n_opt,
    n_mach,
    operation_data,
    machine_data,
    para_lmin,
    para_lmax,
    para_p,
    para_h,
    para_w,
    para_delta,
    para_a,
    para_mach_capacity,
) = load_data()

n_opt = n_opt_selected

# para_p_horizon = np.copy(para_p[:n_opt_selected, :])
# para_p_horizon[para_p_horizon == np.inf] = 0
# # para_h = np.empty((n_opt, n_mach), dtype=object)
# para_h_horizon = np.copy(para_h[:n_opt_selected, :])
# para_h_horizon[para_h_horizon == np.inf] = 0
# para_lmax_horizon = np.copy(para_lmax[:n_opt_selected, :n_opt_selected])
# para_lmax_horizon[para_lmax_horizon == np.inf] = 0
# horizon = (
#     np.sum(para_p_horizon, axis=1)
#     + np.sum(para_h_horizon, axis=1)
#     + np.sum(para_lmax_horizon, axis=1)
# )
# horizon = int(np.sum(horizon)) + 1
# para_lmin[para_lmin == -np.inf] = -infinity
# para_lmin[para_lmin == np.inf] = infinity
# para_lmax[para_lmax == np.inf] = infinity
# para_lmax[para_lmax == -np.inf] = -infinity
# para_p[para_p == np.inf] = infinity
# para_p[para_p == -np.inf] = -infinity
# para_w[para_w == np.inf] = infinity
# para_w[para_w == -np.inf] = -infinity
# para_a[para_a == np.inf] = infinity
# para_a[para_a == -np.inf] = -infinity
# =====================================================
# convert all the numpy arrays with integers data type
# para_lmin = para_lmin.astype(int)
# para_lmax = para_lmax.astype(int)
# para_p = para_p.astype(int)
# para_w = para_w.astype(int)
# para_a = para_a.astype(int)
# para_delta = para_delta.astype(int)
# para_mach_capacity = para_mach_capacity.astype(int)
para_lmin = para_lmin[:n_opt_selected, :n_opt_selected]
para_lmax = para_lmax[:n_opt_selected, :n_opt_selected]
para_p = para_p[:n_opt_selected, :]
para_h = para_h[:n_opt_selected, :]
para_w = para_w[:n_opt_selected, :]
para_a = para_a[:n_opt_selected, :n_opt_selected, :]
# machines
machines = [str(i) for i in range(n_mach)]
# operations
operations = [str(i) for i in range(n_opt_selected)]
# operations = operations[:n_opt_selected]
# machines = machines[:n_mach]
# =====================================================

print("solve the MILP problem with FJSS3")

para_a = np.einsum("mij->ijm", para_a)
# time the running time for the MILP model
# start_time = time.time()

# big_m_fw = get_m_value_runzhong(
#     para_p=para_p, para_h=para_h, para_lmin=para_lmin, para_a=para_a
# )
# print(f"big_m_fw={big_m_fw}")
# print(f"type of big_m_fw is {type(big_m_fw)}")

fjss3 = FJSS3(
    operations=operations,
    machines=machines,
    para_p=para_p,
    para_a=para_a,
    para_w=para_w,
    para_h=para_h,
    para_delta=para_delta,
    para_mach_capacity=para_mach_capacity,
    para_lmin=para_lmin,
    para_lmax=para_lmax,
    precedence=None,
    model_string=None,
    inf_milp=infinity,
    num_workers=4,
    verbose=True,
    # big_m=3315,
    # big_m=None,
)
fjss3.build_model_gurobi()
# print("big_m from fjss3", fjss3.big_m)
fjss3.solve_gurobi()
# running_time = time.time() - start_time

# %%

if fjss3.status == pywraplp.Solver.OPTIMAL:
    print("check if the constraints are met")

    solver = fjss3.solver
    model = fjss3._model

    # %%

    # %%
    def get_values(var):
        return var.solution_value()

    v_get_values = np.vectorize(get_values)

    var_y = v_get_values(fjss3.var_y)
    var_s = v_get_values(fjss3.var_s)
    var_c = v_get_values(fjss3.var_c)
    var_c_max = fjss3.var_c_max
    var_x = v_get_values(fjss3.var_x)
    var_z = v_get_values(fjss3.var_z)

    # check_constraints_cp(
    #     var_y=var_y,
    #     var_s=var_s,
    #     var_c=var_c,
    #     var_c_max=var_c_max,
    #     var_u=None,
    #     operations=operations,
    #     machines=machines,
    #     para_p=para_p,
    #     para_a=para_a,
    #     para_w=para_w,
    #     para_h=para_h,
    #     para_delta=para_delta,
    #     para_mach_capacity=para_mach_capacity,
    #     para_lmin=para_lmin,
    #     para_lmax=para_lmax,
    #     num_t=None,
    # )

    # %%
    # para_a[:, :, :] = -infinity

    big_m = fjss3.big_m

    check_constraints_milp(
        var_y=var_y,
        var_s=var_s,
        var_c=var_c,
        var_c_max=var_c_max,
        operations=operations,
        machines=machines,
        para_p=fjss3.para_p,
        para_a=fjss3.para_a,
        para_w=fjss3.para_w,
        para_h=fjss3.para_h,
        para_delta=fjss3.para_delta,
        para_mach_capacity=fjss3.para_mach_capacity,
        para_lmin=fjss3.para_lmin,
        para_lmax=fjss3.para_lmax,
        big_m=fjss3.big_m,
        var_x=var_x,
        var_z=var_z,
    )
    print("the solutions met the constraints")

else:
    print("no optimal solution found")
