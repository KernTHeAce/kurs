from random import uniform
import Training_Report as TR
import warnings
import copy

warnings.filterwarnings('ignore')


class MLP:
    def __init__(self, input_layer, hidden_layer, output_layer, functions):

        self.hidden_layer_activation = functions[0][0]
        self.d_hidden_layer_activation = functions[0][1]
        self.output_layer_activation = functions[1][0]
        self.d_output_layer_activation = functions[1][1]

        self.inputL = input_layer
        self.hiddenL = hidden_layer
        self.outputL = output_layer

        border = 1 / (hidden_layer ** 0.5)
        self.W_ij = [[uniform(-1 * border, border) for j in range(hidden_layer)] for i in range(input_layer)]
        self.W_jk = [[uniform(-1 * border, border) for k in range(output_layer)] for j in range(hidden_layer)]
        self.W_ij_past = copy.deepcopy(self.W_ij)
        self.W_jk_past = copy.deepcopy(self.W_jk)
        self.T_j = [uniform(-1 * border, border) for j in range(hidden_layer)]
        self.T_k = [uniform(-1 * border, border) for k in range(output_layer)]

        self.report = TR.Report()

    def fit(self, dataset, dataset_size):
        print('Forecasting...')
        result = []
        E = 0
        for index in range(dataset_size):
            X = dataset['x'][index]
            e = dataset['e'][index]

            calc_res = self.calculating(X)
            result.append(calc_res['Z'])
            e1 = self.error(calc_res['Z'], e)
            self.report.add_test_error_value(e1)
            E += e1

        print('Done')
        return result, E

    def calculating(self, X):
        Y = []
        Sy = [0] * self.hiddenL

        Z = []
        Sz = [0] * self.outputL

        for j in range(self.hiddenL):
            for i in range(self.inputL):
                Sy[j] += X[i] * self.W_ij[i][j]
            Sy[j] -= self.T_j[j]
            Y.append(self.hidden_layer_activation(Sy[j]))

        for k in range(self.outputL):
            for j in range(self.hiddenL):
                Sz[k] += Y[j] * self.W_jk[j][k]
            Sz[k] -= self.T_k[k]
            Z.append(self.output_layer_activation(Sz[k]))

        return {'Z': Z, 'Y': Y, 'Sy': Sy, 'Sz': Sz}

    def validation(self, dataset):
        E = 0
        for index in range(len(dataset['x'])):
            x = dataset['x'][index]
            e = dataset['e'][index]

            calc_res = self.calculating(x)

            E += self.error(calc_res['Z'], e)
        self.report.add_validation_error_value(E)
        return E

    @staticmethod
    def error(Z, e):
        error = 0
        for j in range(len(Z)):
            error += (abs(Z[j] - e[j])) ** 2
        error /= 2
        return error

    def learning(self, data_set, constants):
        print('Network learning...')
        dataset = data_set.learning_set
        validation_set = data_set.validation_set

        epoch = 0
        while True:
            for index in range(len(dataset['x']) - 1):
                X_train = dataset['x'][index]
                e_train = dataset['e'][index]

                calc_res = self.calculating(X_train)
                self.modifying(calc_res, X_train, e_train, constants)

                E = 0
                for i in range(len(dataset['x']) - 1):
                    X_check = dataset['x'][i]
                    e_check = dataset['e'][i]

                    calc_res = self.calculating(X_check)
                    E += self.error(calc_res['Z'], e_check)

                self.report.add_learning_error_value(E)
                print(E)
                if E < constants['max_error']:
                    return 'max_error'

                epoch += 1

                val_error = self.validation(validation_set)
                if val_error < constants['validation_error']:
                    return 'validation_error'

    def modifying(self, data, X, e, constants):
        gamma_k = []
        gamma_j = [0] * self.hiddenL

        Z = data['Z']
        Y = data['Y']
        Sy = data['Sy']
        Sz = data['Sz']

        tmp_ij = copy.deepcopy(self.W_ij)
        tmp_jk = copy.deepcopy(self.W_jk)

        for k in range(self.outputL):
            gamma_k.append(Z[k] - e[k])

        for j in range(self.hiddenL):
            for k in range(self.outputL):
                gamma_j[j] += gamma_k[k] * self.d_output_layer_activation(Sy[j]) * self.W_jk[j][k]

        for k in range(self.outputL):
            sgd = constants['alpha'] * gamma_k[k] * self.d_output_layer_activation(Sz[k])
            for j in range(self.hiddenL):
                weight_decay = self.W_jk[j][k] * (1 - constants['lambda'])
                heavy_ball = constants['beta'] * (self.W_jk[j][k] - self.W_jk_past[j][k])
                self.W_jk[j][k] = weight_decay - sgd * Y[j] + heavy_ball
            self.T_k[k] += sgd

        for j in range(self.hiddenL):
            sgd = constants['alpha'] * gamma_j[j] * self.d_hidden_layer_activation(Sy[j])
            for i in range(self.inputL):
                weight_decay = self.W_ij[i][j] * (1 - constants['lambda'])
                heavy_ball = constants['beta'] * (self.W_ij[i][j] - self.W_ij_past[i][j])
                self.W_ij[i][j] = weight_decay - sgd * X[i] + heavy_ball
            self.T_j[j] += sgd

        self.W_jk_past = copy.deepcopy(tmp_jk)
        self.W_ij_past = copy.deepcopy(tmp_ij)
