from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib
import random
import time
import box
import os


P_MUTATION = 0.2
P_CROSSOVER = 0.8
POPULATION_SIZE = 100
GENERATION_SIZE = 10
ECONOMY = 0.3

st = time.time()

matplotlib.use('TkAgg')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
appliances_df = pd.read_csv("Appliances-re-mix-1.csv", sep=";", index_col="appliance")
appliances_df.fillna(0, inplace=True)

type_df = appliances_df.iloc[:,:1]
consumption_df = appliances_df.iloc[:,1:]
length = len(consumption_df.columns)
height = len(consumption_df.index)
print("cons")
print(consumption_df)

gene, meta, groups, electricity = box.sandwich(consumption_df)
print("gg")
print(gene)
print("mm", meta)
print(groups)
print(electricity)
genome = box.to_genome(gene, meta)
print("genome")
print(genome)
prices = box.get_prices()
bill = 0
for i in range(height):
    price = box.get_bill(genome[i], electricity[i], prices)
    bill += price
print("STOCK BILL:", bill)
aim = bill * (1 - ECONOMY)
print("AIM: ", aim)

print(groups)
def create_individual():
    local_gene = list()
    copy_genome = genome.copy()
    # print(copy_genome)
    for i in range(height):
        if type_df.iloc[i, 0] == 0:
            local_gene.extend(box.flatten_list(copy_genome[i]))
        elif type_df.iloc[i, 0] == 1:
            # print("to1")
            shake_list = box.shake_switches(box.flatten_list(copy_genome[i]), ECONOMY)
            local_gene.extend(shake_list)
        elif type_df.iloc[i, 0] == 2:
            # print("to2")
            shake_gr_list = box.shake_group_switches(genome[i], groups[i], ECONOMY)
            shake_list = box.shake_positions(shake_gr_list, groups[i], length, ECONOMY)
            local_gene.extend(shake_list)
    return local_gene

# print(genome[2])
# tt = box.shake_group_switches(genome[2], groups[2], 0.7)
# print(tt)

def create_population():
    population = []
    for _ in range(POPULATION_SIZE):
        population.append(create_individual())
    return population


weights = {"sd": 10}



def get_info(ind):
    ind_copy = ind.copy()
    local_genome = box.to_genome(ind_copy, meta)
    fine = 0
    local_bill = 0
    error_1 = 0
    error_2 = 0
    error_3 = 0
    for i in range(len(type_df["type"])):
        if type_df.iloc[i, 0] == 0:
            t_price = box.get_bill(local_genome[i], electricity[i], prices)
            local_bill += t_price
        elif type_df.iloc[i, 0] == 1:
            error_1 += box.rule_1(local_genome[i], 0.1, True)
            error_2 += box.rule_2(local_genome[i], groups[i], 0.3, True)
        elif type_df.iloc[i, 0] == 2:
            error_1 += box.rule_1(local_genome[i], 0.2)
            error_3 += box.rule_3(local_genome[i], groups[i], 0.1, True)
    return error_1, error_2, error_3



def evaluation(ind):
    ind_copy = ind.copy()
    local_genome = box.to_genome(ind_copy, meta)
    fine = 0
    local_bill = 0
    info = [[],[]]
    for i in range(len(type_df["type"])):
        if type_df.iloc[i, 0] == 0:
            t_price = box.get_bill(local_genome[i], electricity[i], prices)
            local_bill += t_price
        elif type_df.iloc[i, 0] == 1:
            fine_1 = box.rule_1(local_genome[i], 0.1)
            fine_2 = box.rule_2(local_genome[i], groups[i], 0.3)
            fine += fine_1 + fine_2
            t_price = box.get_bill(local_genome[i], electricity[i], prices)
            local_bill += t_price
        elif type_df.iloc[i, 0] == 2:
            fine_1 = box.rule_1(local_genome[i], 0.6,0)
            fine_3 = box.rule_3(local_genome[i], groups[i], 0.1)
            fine_4 = box.rule_4(local_genome[i], 200)
            fine_5 = box.rule_5(local_genome[i], groups[i], 200)
            fine += (fine_1 + fine_3 + fine_4 + fine_5)
            t_price = box.get_bill(local_genome[i], electricity[i], prices)
            local_bill += t_price
    fine_6 = box.rule_6(aim, local_bill, 50)
    fine += fine_6
    return fine

# evaluation(inda)




def select_parent(population):
    # CAN BE A PROBLEM WITH THE SAME PARENT
    i1 = i2 = i3 = 0
    while i1 == i2 or i1 == i3 or i2 == i3:
        i1, i2, i3 = random.randint(0, len(population)-1), random.randint(0, len(population)-1), random.randint(0, len(population)-1)
        p1 = evaluation(population[i1])
        p2 = evaluation(population[i2])
        p3 = evaluation(population[i3])


        if p1 <= p2 and p1 <= p3:
            return population[i1]
        elif p2 <= p1 and p2 <= p3:
            return population[i2]
        else:
            return population[i3]


def crossover(ind1, ind2):
    ind1_copy = ind1.copy()
    ind2_copy = ind2.copy()
    p = P_CROSSOVER
    local_genome1 = box.to_genome(ind1_copy, meta)
    local_genome2 = box.to_genome(ind2_copy, meta)
    new_gene_1 = []
    new_gene_2 = []
    for i in range(len(type_df["type"])):
        if type_df.iloc[i, 0] == 0:
            new_gene_1.extend(box.flatten_list(local_genome1[i]))
            new_gene_2.extend(box.flatten_list(local_genome2[i]))
        elif type_df.iloc[i, 0] == 1:
            i1, i2, = box.cross_1(local_genome1[i], local_genome2[i], p)
            new_gene_1.extend(box.flatten_list(i1))
            new_gene_2.extend(box.flatten_list(i2))

            # new_gene_1.extend(box.flatten_list(local_genome1[i]))
            # new_gene_2.extend(box.flatten_list(local_genome2[i]))
        elif type_df.iloc[i, 0] == 2:
            i1, i2 = box.cross_2(local_genome1[i], local_genome2[i], groups[i], p)
            new_gene_1.extend(i1)
            new_gene_2.extend(i2)


            # new_gene_1.extend(box.flatten_list(local_genome1[i]))
            # new_gene_2.extend(box.flatten_list(local_genome2[i]))
    return new_gene_1, new_gene_2


def mutation(ind, p):
    # print(ind)
    local_gene = list()
    # local_ind = ind.copy()
    copy_genome = box.to_genome(ind, meta)
    for i in range(height):
        if type_df.iloc[i, 0] == 0:
            # print("to0")
            local_gene.extend(box.flatten_list(copy_genome[i]))
        elif type_df.iloc[i, 0] == 1:
            # print("to1")
            shake_list = box.shake_switches(box.flatten_list(copy_genome[i]), p)
            local_gene.extend(shake_list)
        elif type_df.iloc[i, 0] == 2:
            # print("to2")
            shake_gr_list = box.shake_group_switches(copy_genome[i], groups[i], p)
            shake_list = box.shake_positions(shake_gr_list, groups[i], length, p)
            local_gene.extend(shake_list)
    return local_gene


if __name__ == "__main__":
    pop = create_population()
    best_list = []
    worst_list = []
    for j in range(GENERATION_SIZE):
        print("GENERATION: ", j)
        new_pop = []
        fitness_list = []
        for i in range(int(POPULATION_SIZE/2)):
            parent1 = select_parent(pop)
            parent2 = select_parent(pop)
            if random.random() <= P_CROSSOVER:
                parent1, parent2 = crossover(parent1, parent2)
            if random.random() <= P_MUTATION:
                parent1 = mutation(parent1, 0.01)
                parent2 = mutation(parent2, 0.01)
            new_pop.append(parent1)
            new_pop.append(parent2)
            fitness_list.append(evaluation(parent1))
            fitness_list.append(evaluation(parent2))
        print("BEST VALUE:", min(fitness_list))
        best_ind = new_pop[fitness_list.index(min(fitness_list))]
        # print(best_ind)
        best_list.append(min(fitness_list))
        # print("WORST VALUE:", max(fitness_list))
        worst_ind = new_pop[fitness_list.index(max(fitness_list))]
        worst_list.append(max(fitness_list))
        pop = new_pop
        print("---------------------")

    field = list()
    print("INFO")
    e1, e2, e3 = get_info(best_ind)
    print("error_1: ", e1, "error_2: ", e2, "error_3: ", e3)
    best_genome = box.to_genome(best_ind, meta)
    best_bill = 0
    for i in range(height):
        local_price = box.get_bill(best_genome[i], electricity[i], prices)
        best_bill += local_price
    print("aim price:", aim)
    print("optimized price:", best_bill)
    print("delta:", abs(aim - best_bill))

    print()

    font = {'family': 'Times New Roman',
            'size': 12}

    matplotlib.rc('font', **font)

    print(best_genome)
    for i in range(height):
        field.append(box.turn_line(best_genome[i], length))
    df = pd.DataFrame(field, index=appliances_df.index, columns=consumption_df.columns, dtype = float)

    # Plot solution
    plt.subplots(figsize=(5, 2))
    # plt.title(f"Ekonomijas Koeficients={ECONOMY}")

    # tt = appliances_df.drop("type", axis=1)
    ax = sns.heatmap(df, linewidth=0.5, cmap="YlGnBu", vmin=0, vmax=2, cbar=False)
    ax.set(xlabel="Laiks", ylabel="Ierīces")
    plt.show()

# get the end time
et = time.time()

# # get the execution time
# elapsed_time = et - st
# print('Execution time:', elapsed_time, 'seconds')


# # original heatmap
# field = list()
# for i in range(height):
#     field.append(box.turn_line(genome[i], length))
# df = pd.DataFrame(field, index=appliances_df.index, columns=consumption_df.columns, dtype = float)
#
# # Plot solution
# plt.subplots(figsize=(10, 2))
# plt.title(f"Economy Coefficient={ECONOMY}")
#
# # tt = appliances_df.drop("type", axis=1)
# ax = sns.heatmap(df, linewidth=0.5, cmap="YlGnBu", vmin=0, vmax=2, cbar=False)
# ax.set(xlabel="Time", ylabel="Appliances")
# plt.show()