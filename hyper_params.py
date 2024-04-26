homo_para_1 = {'gamma': 0.99, 'epsilon':0.9, 'alpha':1e-5,
                    'batch_size': 128, 'eps_decay': 5e-5,
                    'replace': 100, 'input_dims':[23], 'n_actions':2,
                    'mem_size' : 100000, 'eps_min':0.01} 

'''para_2 = {'gamma': 0.999, 'epsilon':0.6, 'alpha':1e-6,
                    'batch_size': 256, 'eps_decay': 2e-5,
                    'replace': 100, 'input_dims':[23], 'n_actions':2,
                    'mem_size' : 1000000, 'eps_min':0.01}'''

para_2 = {'gamma': 0.999, 'epsilon':0.6, 'alpha':1e-8,
                    'batch_size': 256, 'eps_decay': 2e-3,
                    'replace': 100, 'input_dims':[23], 'n_actions':2,
                    'mem_size' : 1000000, 'eps_min':0.01} 


single_agent_para = {'gamma': 0.999, 'epsilon':0.9, 'alpha':1e-5,
                    'batch_size': 256, 'eps_decay': 3e-6,
                    'replace': 100, 'input_dims':[23], 'n_actions':2,
                    'mem_size' : 100000, 'eps_min':0.01} 