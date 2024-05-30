from math import ceil
import pandas as pd
import numpy as np
import requests
import random
import io


def detect_groups(data):
    groups = []
    current_group = []
    for i in range(len(data)):
        if data[i] > 0:
            current_group.append(i)
        else:
            if current_group:
                groups.append(current_group)
            current_group = []
    if current_group:
        groups.append(current_group)
    return groups


def sandwich(data):
    a_list = data.to_numpy()
    height = len(a_list)
    length = len(a_list[0])
    groups = list()
    electricity = list()
    meta = [8, []]
    gene = list()
    for i in range(height):
        counter = 0
        # create groups
        groups.append(detect_groups(a_list[i]))
        consumption = list()
        for j in range(length):
            if a_list[i][j] > 0:
                counter += 1
                # electricity unit of item
                consumption.append(a_list[i][j])
                # encode gene
                on = 1
                string = "{0:07b}".format(j)
                pos = [int(x) for x in string]
                gene.append(on)
                gene.extend(pos)
        meta[1].append(counter)
        electricity.append(consumption)
    return gene, meta, groups, electricity


def flatten_list(matrix):
    flat_list = []
    for row in matrix:
        flat_list.extend(row)
    return flat_list


def reshape_list(data, meta):
    reshaped_data = []
    i = 0
    for sublist_len in meta:
        sublist = []
        while i < len(data) and len(sublist) < sublist_len:
            sublist.append(data[i])
            i += 1
        reshaped_data.append(sublist)
    return reshaped_data


def to_genome(beans, meta):
    gene_size = meta[0]
    genes = [beans[i:i + gene_size] for i in range(0, len(beans), gene_size)]
    genome = reshape_list(genes, meta[1])
    return genome


def decoder(data):
    # decode gene to decimal
    for i in range(0, len(data), 8):
        on_off = data[i]
        pos_bin = data[i + 1:i + 8]
        pos_num = int("".join(map(str, pos_bin)))
        pos = int(str(pos_num), 2)
    return on_off, pos


def move(positions, i):
    moved = list()
    for j in range(len(positions)):
        moved.append(positions[j] + i)
    return moved


def shake_positions(gene, groups, length, p):
    # print(gene)
    gene_copy = gene.copy()
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    # decode gene to get on/off list
    turn_list = list()
    pos_list = list()
    for i in range(len(gene_copy)):
        turn, pos = decoder(gene_copy[i])
        turn_list.append(turn)
        pos_list.append(pos)
    # reshape on/off list by groups size
    pos_list = reshape_list(pos_list, length_groups)

    result = []
    for i in range(len(pos_list)):
        if random.random() < p:
            first = pos_list[i][0]
            last = pos_list[i][-1]
            high = length - last - 1
            low = 0 - first
            result.append(move(pos_list[i], random.randint(low, high)))
        else:
            result.append(pos_list[i])

    new_gene = []
    flat_pos = flatten_list(result)
    for i in range(len(turn_list)):
        on = turn_list[i]
        string = "{0:07b}".format(flat_pos[i])
        pos = [int(x) for x in string]
        new_gene.append(on)
        new_gene.extend(pos)
    return new_gene


def shake_switches(gene, p):
    local_gene = gene.copy()
    for i in range(0, len(local_gene), 8):
        if random.random() < p:
            local_gene[i] = 1 - local_gene[i]
    return local_gene


def shake_group_switches(gene, groups, p):
    # print(gene)
    gene_copy = gene.copy()
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    # decode gene to get on/off list
    turn_list = list()
    pos_list = list()
    for i in range(len(gene_copy)):
        turn, pos = decoder(gene_copy[i])
        turn_list.append(turn)
        pos_list.append(pos)
    # reshape on/off list by groups size
    turn_list = reshape_list(turn_list, length_groups)
    for i in range(len(turn_list)):
        if random.random() < p:
            for j in range(len(turn_list[i])):
                turn_list[i][j] = 1 - turn_list[i][j]

    new_gene = []
    flat_turn = flatten_list(turn_list)
    for i in range(len(flat_turn)):
        on = flat_turn[i]
        string = "{0:07b}".format(pos_list[i])
        pos = [int(x) for x in string]
        temp_list = list()
        temp_list.append(on)
        temp_list.extend(pos)
        new_gene.append(temp_list)
    return new_gene


def turn_line(gene, length):
    line = [0] * length
    turn_gene = list()
    pos_gene = list()
    for unit in gene:
        turn, pos = decoder(unit)
        turn_gene.append(turn)
        pos_gene.append(pos)
    for i in range(len(pos_gene)):
        if turn_gene[i] == 1:
            if pos_gene[i] < 96:
                line[pos_gene[i]] = 1

        if turn_gene[i] == 0:
            if pos_gene[i] < 96:
                line[pos_gene[i]] = 2
    return line


def rule_1(gene, penalty, info=False):
    counter = 0
    for i in range(len(gene)):
        if gene[i][0] == 0:
            counter += 1
    fine = counter * penalty
    if info:
        return counter
    else:
        return fine


def rule_2(gene, groups, penalty, info=False):
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    # decode gene to get on/off list
    on_off_list = list()
    for i in range(len(gene)):
        on_off, pos = decoder(gene[i])
        on_off_list.append(on_off)
    # reshape on/off list by groups size
    on_off_list = reshape_list(on_off_list, length_groups)
    indent_sum = 0
    # calculate indent
    for values in on_off_list:
        length = len(values)
        zero_count = values.count(0)
        if zero_count > 0:
            # P.D.
            # (33 - 9) / 9 = 2
            # (9 * 2) + ((33-9) - 2) = 18 + 22 = 40

            # Kondik 1
            # (24 - 7) / 7 = 2
            # (7 * 2) + ((24 - 7) - 2) = 14 + 15 = 29

            # Kondik 2
            # (5 - 2) / 2 = 1
            # (2 * 1) + ((5 - 2) - 1) = 2 + 2 = 4

            # Holod
            # (96 - 30) / 30 = 2
            # (30 * 2) + ((96 - 30) - 2) = 60 + 64 = 124
            # 40 + 29 + 4 + 124 = 197


            # eg1
            # (18 - 6) / 6 = 2
            # (6 * 2) + ((18 - 6) - 2) = 12 + 10 = 22

            # eg2
            # (27 - 9) / 9 = 2
            # (9 * 2) + ((27 - 9) - 2) = 18 + 16 = 34

            # v1
            # (37 - 13) / 13 = 2
            # (13 * 2) + ((37 - 13) - 2) = 26 + 22 = 48

            # v2
            # (30 - 17) / 17 = 1
            # (17 * 1) + ((30 - 17) - 1) = 17 + 12 = 29



            # 3
            # (30 - 13) / 13 = 2
            # (13 * 2) + ((30 - 13) - 2) = 26 + 15 = 41

            # count what span should be ideal for this group
            span = ceil((length - zero_count) / (zero_count))
            # count spans for this group
            result = []
            counter = 0
            for i in values:
                if i == 1:
                    counter += 1
                else:
                    result.append(counter)
                    counter = 0

            # count spans difference from ideal span
            counter = 0
            for i in result:
                counter += abs(span - i)
            indent_sum += counter
    fine = indent_sum * penalty
    if info:
        return indent_sum
    else:
        return fine


def rule_3(gene, groups, penalty, info=False):
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    # decode gene to get pos list
    pos_list = list()
    for i in range(len(gene)):
        on_off, pos = decoder(gene[i])
        pos_list.append(pos)
    # reshape pos list by groups size
    pos_item = reshape_list(pos_list, length_groups)
    # print(pos_item)

    span_list = list()
    for i in range(len(pos_item)):
        k_sublist = list()
        for j in range(len(pos_item[i])):
            k_sublist.append(pos_item[i][j] - groups[i][j])
        # print("k-sub:", k_sublist)
        span_list.append(k_sublist[0])
    counter_mistakes = 0
    for val in span_list:
        counter_mistakes += abs(val)
    # for span_sublist in span_list:
    #     counter_mistakes += sum(abs(number) for number in span_sublist)
    fine = counter_mistakes * penalty
    if info:
        return counter_mistakes
    else:
        return fine


def rule_4(gene, penalty):
    # decode gene to get pos list
    pos_list = list()
    for i in range(len(gene)):
        on_off, pos = decoder(gene[i])
        pos_list.append(pos)
    pos_set = set(pos_list)
    duplicates = len(pos_list) - len(pos_set)
    fine = duplicates * penalty
    return fine


def rule_5(gene, groups, penalty):
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    # decode gene to get on/off list
    on_off_list = list()
    for i in range(len(gene)):
        on_off, pos = decoder(gene[i])
        on_off_list.append(on_off)
    # reshape on/off list by groups size
    on_off_list = reshape_list(on_off_list, length_groups)

    bool_list = list()
    for on_off_sublist in on_off_list:
        # bool_list.append(all(i == 1 for i in on_off_sublist))
        bool_list.append(len(set(on_off_sublist)) == 1)
    counter_mistakes = bool_list.count(False)
    fine = counter_mistakes * penalty
    return fine


def rule_6(aim, local_bill, penalty):
    # print("AIM:", aim)
    # print("LOCAL BILL:", local_bill)
    # print("kick:", kick)
    fine = (abs(aim - local_bill) * penalty)
    return fine


def get_prices():
    # today = datetime.date.today()
    # tomorrow = today + datetime.timedelta(days=1)
    today = "2024-04-08"
    tomorrow = "2024-04-09"

    url = f"https://dashboard.elering.ee/api/nps/price/csv?start={today}T20%3A59%3A59.999Z&end={tomorrow}T20%3A59%3A59.999Z&fields=lv"
    r = requests.get(url)
    r = r.content

    raw_data = pd.read_csv(io.StringIO(r.decode('latin-1')), sep=";", decimal=",")
    raw_data = raw_data.drop(raw_data.columns[[0, 1]], axis=1)
    prices_MWh = raw_data.iloc[:, 0].to_numpy()
    prices_KWh = prices_MWh / 1000

    prices_dict = dict()
    counter = 0
    for i in range(24):
        for j in range(4):
            prices_dict[counter] = prices_KWh[i]
            counter += 1
    return prices_dict


def get_pv():
    pv = [0, 0, 0, 0, 0, 0, 0.002, 0.004, 0.006, 0.008, 0.008, 0.008, 0.007, 0.006, 0.007, 0.006, 0.005,
          0.004, 0.003, 0.002, 0, 0, 0, 0]
    pv_dict = dict()
    counter = 0
    for i in range(24):
        for j in range(4):
            pv_dict[counter] = pv[i]
            counter += 1
    return pv_dict


def get_bill(gene, electricity, prices):
    turn_gene = list()
    pos_gene = list()
    pv_list = get_pv()
    price = 0
    for unit in gene:
        turn, pos = decoder(unit)
        turn_gene.append(turn)
        pos_gene.append(pos)
    for i in range(len(pos_gene)):
        price += (prices[pos_gene[i]] * (electricity[i] - pv_list[i])) * turn_gene[i]
    return price


def cross_1(ind1, ind2, p):
    for i in range(len(ind2)):
        if random.random() < p:
            ind1[i][0], ind2[i][0] = ind2[i][0], ind1[i][0]
    return ind1, ind2


def cross_2(ind1, ind2, groups, p):
    # length of each group
    length_groups = []
    for group in groups:
        length_groups.append(len(group))

    turn_1_list = list()
    pos_1_list = list()
    for i in range(len(ind1)):
        turn, pos = decoder(ind1[i])
        turn_1_list.append(turn)
        pos_1_list.append(pos)
    pos_1_list = reshape_list(pos_1_list, length_groups)

    turn_2_list = list()
    pos_2_list = list()
    for i in range(len(ind2)):
        turn, pos = decoder(ind2[i])
        turn_2_list.append(turn)
        pos_2_list.append(pos)
    pos_2_list = reshape_list(pos_2_list, length_groups)

    for i in range(len(pos_1_list)):
        if random.random() < p:
            turn_1_list[i], turn_2_list[i] = turn_2_list[i], turn_1_list[i]
        if random.random() < p:
            pos_1_list[i], pos_2_list[i] = pos_2_list[i], pos_1_list[i]

    new_gene1 = []
    flat_1_pos = flatten_list(pos_1_list)
    for i in range(len(turn_1_list)):
        on = turn_1_list[i]
        string = "{0:07b}".format(flat_1_pos[i])
        pos = [int(x) for x in string]
        new_gene1.append(on)
        new_gene1.extend(pos)

    new_gene2 = []
    flat_2_pos = flatten_list(pos_2_list)
    for i in range(len(turn_2_list)):
        on = turn_2_list[i]
        string = "{0:07b}".format(flat_2_pos[i])
        pos = [int(x) for x in string]
        new_gene2.append(on)
        new_gene2.extend(pos)

    return new_gene1, new_gene2
