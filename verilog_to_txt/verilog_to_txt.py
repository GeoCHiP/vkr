import re
import glob
import json
import argparse
import os
from pathlib import Path

import networkx as nx
from scipy.sparse import coo_array, block_diag
from tqdm import tqdm

from verilog_to_graph import parser, grapher


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-d',
        '--dataset-path',
        default='verilog_dataset',
        help='path to the verilog dataset directory',
    )
    parser.add_argument(
        '-p',
        '--prefix',
        default='combcirc',
        help='output file names prefix',
    )
    parser.add_argument(
        '-o',
        '--output-directory',
        default='combcirc',
        help='output files directory',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print out additional information',
    )
    args = parser.parse_args()

    return args


def add_to_dict(target_dict: dict, lst: list) -> None:
    for element in lst:
        if element not in target_dict:
            target_dict[element] = len(target_dict)


class CombcircDataset:
    def __init__(self, path: str, verbose: bool = False):
        self.path = path
        self.verbose = verbose
        self.block_diag_adj_mat = coo_array((0, 0))
        self.graph_indicator = []
        self.graph_labels = []

        self.n_lbl_to_id = {}
        self.e_lbl_to_id = {}
        self.node_ids = []
        self.edge_ids = []

    def _get_reliability(self, json_filepath: str) -> float:
        json_data = Path(json_filepath).read_text()
        graph_info = json.loads(json_data)
        return graph_info['reliability']

    def read_graphs(self):
        self.num_graphs = len(list(glob.iglob(f'{self.path}/*/*/*.v')))
        with tqdm(total=self.num_graphs) as pbar:
            for i, filepath in enumerate(glob.iglob(f'{self.path}/*/*/*.v')):
                pbar.set_description_str(filepath)

                reliability = self._get_reliability(f'{filepath[:-2]}.json')

                in_n, out_n, nodes, edges = parser(filepath)
                DG = grapher(in_n, out_n, nodes, edges)

                adj_mat = nx.to_scipy_sparse_array(DG, format='coo')

                self.block_diag_adj_mat = block_diag((self.block_diag_adj_mat, adj_mat))
                self.graph_indicator.extend([i for _ in range(adj_mat.shape[0])])
                self.graph_labels.append(reliability)

                if self.verbose and ' ' in DG.nodes:
                    print("found ' ' in", filepath)

                labels_pattern = r'^(.+?)\d+$'

                node_labels = [re.sub(labels_pattern, r'\1', n) for n in DG.nodes]
                add_to_dict(self.n_lbl_to_id, node_labels)
                self.node_ids.extend([self.n_lbl_to_id[lbl] for lbl in node_labels])

                edge_labels = [(re.sub(labels_pattern, r'\1', e[0]), re.sub(labels_pattern, r'\1', e[1])) for e in DG.edges]
                add_to_dict(self.e_lbl_to_id, edge_labels)
                self.edge_ids.extend([self.e_lbl_to_id[lbl] for lbl in edge_labels])

                pbar.update(1)

        self.num_edges = self.block_diag_adj_mat.count_nonzero()
        self.num_nodes = self.block_diag_adj_mat.shape[0]

    def write_dataset(self, output_directory: str, prefix: str):
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        with open(f'{output_directory}/{prefix}_A.txt', 'w') as ofile:
            n = 0
            for edge in zip(self.block_diag_adj_mat.row, self.block_diag_adj_mat.col):
                ofile.write(f'{edge[0] + 1}, {edge[1] + 1}\n')
                n += 1

            assert n == self.num_edges

        with open(f'{output_directory}/{prefix}_graph_indicator.txt', 'w') as ofile:
            n = 0
            for graph_i in self.graph_indicator:
                ofile.write(f'{graph_i + 1}\n')
                n += 1

            assert n == self.num_nodes

        with open(f'{output_directory}/{prefix}_graph_attributes.txt', 'w') as ofile:
            n = 0
            for val in self.graph_labels:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_graphs

        with open(f'{output_directory}/{prefix}_node_labels.txt', 'w') as ofile:
            n = 0
            for val in self.node_ids:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_nodes

        with open(f'{output_directory}/{prefix}_edge_labels.txt', 'w') as ofile:
            n = 0
            for val in self.edge_ids:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_edges

        with open(f'{output_directory}/{prefix}_node_labels_mapping.txt', 'w') as ofile:
            ofile.write('Node labels:\n\n')
            for lbl, lbl_id in self.n_lbl_to_id.items():
                ofile.write(f' {lbl_id}  "{lbl}"\n')

        with open(f'{output_directory}/{prefix}_edge_labels_mapping.txt', 'w') as ofile:
            ofile.write('Edge labels:\n\n')
            for lbl, lbl_id in self.e_lbl_to_id.items():
                ofile.write(f' {lbl_id}  "{lbl}"\n')

        if self.verbose:
            print(f'{self.path}: done.')
            print(f'Processed:')
            print(f'{self.num_graphs} graphs')
            print(f'{self.num_nodes} nodes')
            print(f'{self.num_edges} edges')


class ISCADataset:
    def __init__(self, path: str, verbose: bool = False):
        self.path = path
        self.verbose = verbose
        self.block_diag_adj_mat = coo_array((0, 0))
        self.graph_indicator = []
        self.graph_labels = []

        self.n_lbl_to_id = {}
        self.e_lbl_to_id = {}
        self.node_ids = []
        self.edge_ids = []

        # https://github.com/RomeoMe5/CAD_Combinational_Circuits/blob/master/Dataset/dataset_ISCAS85.csv
        self.reliability_map = {
            'c17': 0.7419,
            'c432': 0.3128,
            'c499': 0.5333,
            'c880': 0.5,  # dunno
            'c1355': 0.5345,
            'c1908': 0.617,
            'c2670': 0.5,  # dunno
            'c3540': 0.3442,
            'c5315': 0.5,  # dunno
            'c6288': 0.5,  # dunno
            'c7552': 0.5,  # dunno
        }

    def _get_reliability(self, circuit_name: str) -> float:
        return self.reliability_map[circuit_name]

    def read_graphs(self):
        from circuitgraph.io import bench_to_circuit

        self.num_graphs = len(list(glob.iglob(f'{self.path}/*.bench')))
        with tqdm(total=self.num_graphs) as pbar:
            for i, filepath in enumerate(glob.iglob(f'{self.path}/*.bench')):
                pbar.set_description_str(filepath)

                circuit_name = os.path.split(filepath)[-1][:-6]
                reliability = self._get_reliability(circuit_name)

                netlist_code = Path(filepath).read_text()
                DG = bench_to_circuit(netlist_code, circuit_name).graph

                adj_mat = nx.to_scipy_sparse_array(DG, format='coo')

                self.block_diag_adj_mat = block_diag((self.block_diag_adj_mat, adj_mat))
                self.graph_indicator.extend([i for _ in range(adj_mat.shape[0])])
                self.graph_labels.append(reliability)

                if self.verbose and ' ' in DG.nodes:
                    print("found ' ' in", filepath)

                labels_pattern = r'^(.+?)_(.*)$'

                node_labels = [re.sub(labels_pattern, r'\1', n) for n in DG.nodes]
                add_to_dict(self.n_lbl_to_id, node_labels)
                self.node_ids.extend([self.n_lbl_to_id[lbl] for lbl in node_labels])

                edge_labels = [(re.sub(labels_pattern, r'\1', e[0]), re.sub(labels_pattern, r'\1', e[1])) for e in DG.edges]
                add_to_dict(self.e_lbl_to_id, edge_labels)
                self.edge_ids.extend([self.e_lbl_to_id[lbl] for lbl in edge_labels])

                pbar.update(1)

        self.num_edges = self.block_diag_adj_mat.count_nonzero()
        self.num_nodes = self.block_diag_adj_mat.shape[0]

    def write_dataset(self, output_directory: str, prefix: str):
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        with open(f'{output_directory}/{prefix}_A.txt', 'w') as ofile:
            n = 0
            for edge in zip(self.block_diag_adj_mat.row, self.block_diag_adj_mat.col):
                ofile.write(f'{edge[0] + 1}, {edge[1] + 1}\n')
                n += 1

            assert n == self.num_edges

        with open(f'{output_directory}/{prefix}_graph_indicator.txt', 'w') as ofile:
            n = 0
            for graph_i in self.graph_indicator:
                ofile.write(f'{graph_i + 1}\n')
                n += 1

            assert n == self.num_nodes

        with open(f'{output_directory}/{prefix}_graph_attributes.txt', 'w') as ofile:
            n = 0
            for val in self.graph_labels:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_graphs

        with open(f'{output_directory}/{prefix}_node_labels.txt', 'w') as ofile:
            n = 0
            for val in self.node_ids:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_nodes

        with open(f'{output_directory}/{prefix}_edge_labels.txt', 'w') as ofile:
            n = 0
            for val in self.edge_ids:
                ofile.write(f'{val}\n')
                n += 1

            assert n == self.num_edges

        with open(f'{output_directory}/{prefix}_node_labels_mapping.txt', 'w') as ofile:
            ofile.write('Node labels:\n\n')
            for lbl, lbl_id in self.n_lbl_to_id.items():
                ofile.write(f' {lbl_id}  "{lbl}"\n')

        with open(f'{output_directory}/{prefix}_edge_labels_mapping.txt', 'w') as ofile:
            ofile.write('Edge labels:\n\n')
            for lbl, lbl_id in self.e_lbl_to_id.items():
                ofile.write(f' {lbl_id}  "{lbl}"\n')

        if self.verbose:
            print(f'{self.path}: done.')
            print(f'Processed:')
            print(f'{self.num_graphs} graphs')
            print(f'{self.num_nodes} nodes')
            print(f'{self.num_edges} edges')


def main():
    args = parse_args()

    # cd = CombcircDataset(args.dataset_path, args.verbose)
    # cd.read_graphs()
    # cd.write_dataset(args.output_directory, args.prefix)
    isca = ISCADataset(args.dataset_path, args.verbose)
    isca.read_graphs()
    isca.write_dataset(args.output_directory, args.prefix)


if __name__ == '__main__':
    main()
