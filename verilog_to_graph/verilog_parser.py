def parser(file_, verbose=0):
    GATES = ['not', 'and', 'or', 'nand', 'nor', 'xor', 'xnor', 'buf', 'assign']
    # all input ports are taken as nodes to visualize better
    input_nodes = []
    # all output ports are taken as nodes to visualize better
    output_nodes = []
    # nodes
    gates = []
    # [edges][(tail, head)] here the first index is the name of the wire;
    # tail and head are the nodes to which the edge is connected to
    wires = []

    v_file = open(file_, 'r')
    n = 0
    line = v_file.readline()
    while line:
        # remove all leading spaces
        line = line.lstrip()

        if line.startswith('//') or line.startswith('module'):
            pass
        elif line.startswith('input'):
            # find all the input ports
            line = line.lstrip('input').split(sep=',')[:-1]
            line = [x.strip(',;\n ') for x in line]
            input_nodes.extend(line)
        elif line.startswith('output'):
            # find all the output ports
            line = line.lstrip('output').split(sep=',')
            line = [x.strip(',;\n ') for x in line]
            output_nodes.extend(line)
        elif line.startswith('assign'):
            gate = 'assign' + str(n)
            n += 1
            gates.append(gate)

            line = ''.join(line.split(' ')[1:])[:-1]
            line = (line[:-1]).split('=')

            _output = line[0]
            _input = line[1:]

            if _output in output_nodes:
                wires.append([_output, gate, [_output]])
            else:
                flag = False
                for i in wires:
                    if i[0] == _output:
                        i[1] = gate
                        flag = True
                        break
                if not flag:
                    wires.append([_output, gate, []])

            for i in _input:
                # print(i, end='')
                if i in input_nodes:
                    flag = False
                    for j in wires:
                        if j[0] == i:
                            j[2].append(gate)
                            flag = True
                            break
                    if not flag:
                        wires.append([i, i, [gate]])
                else:
                    flag = False
                    for j in wires:
                        if j[0] == i:
                            j[2].append(gate)
                            flag = True
                            break
                    if not flag:
                        wires.append([i, ' ', [gate]])
        elif any(g in line for g in GATES):
            # find all the connections and gates

            # remove gate type (gate instantiation) from line
            stri = ''
            line = (line.split(sep=' ', maxsplit=1))
            g = line[0]
            line = line[1:]
            line = stri.join(line)

            # extract gate name from line, append to gates and remove from line
            line = line.split('(')
            gate = g + str(n) + (line[0]).strip(',;\n ()')
            n = n + 1
            gates.append(gate)
            line = line[1:]

            # extract input and output ports of gate and append wires
            stri = ''
            line = stri.join(line)
            line = [x.strip(',;\n ()') for x in line.split(',')]
            _output = line[0]
            _input = line[1:]


            # print(_output, _input)
            # checking if a wire exists in wires with name _output and adding its edge parameters
            if _output in output_nodes:
                wires.append([_output, gate, [_output]])
            else:
                flag = 0
                for i in wires:
                    if(i[0] == _output):
                        i[1] = gate
                        flag = 1
                        break

                if flag == 0:
                    wires.append([_output, gate, []])

            for i in _input:
                # print(i, end='')
                if i in input_nodes:
                    flag = 0
                    for j in wires:
                        if j[0] == i:
                            j[2].append(gate)
                            flag = 1
                            break
                    if flag == 0:
                        wires.append([i, i, [gate]])

                else:
                    flag = 0
                    for j in wires:
                        if(j[0] == i):
                            j[2].append(gate)
                            flag = 1
                            break

                    if flag == 0:
                        wires.append([i, ' ', [gate]])

        line = v_file.readline()

    return input_nodes, output_nodes, gates, wires
