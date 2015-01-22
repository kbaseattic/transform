def read_configs(configs_directory):
    configs = dict()

    for x in os.listdir(configs_directory):
        with open(os.path.join(configs_directory,x), 'r') as f:
            c = simplejson.loads(f.read())
            configs[c["script_type"]] = c

    return configs


