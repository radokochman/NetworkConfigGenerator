import csv
import os

try:
    from jinja2 import Template
except Exception:
    print('Error while importing jinja2 library. Please make sure it\'s present on your workstation.')
    input('Press enter to exit...')
    exit(1)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CISCO_INTERFACE_TEMPLATE_PATH = '{root_dir}/templates/cisco_interface.j2'.format(root_dir=ROOT_DIR)
CISCO_VLAN_TEMPLATE_PATH = '{root_dir}/templates/cisco_vlan.j2'.format(root_dir=ROOT_DIR)
DELL_INTERFACE_TEMPLATE_PATH = '{root_dir}/templates/dell_interface.j2'.format(root_dir=ROOT_DIR)
DELL_VLAN_TEMPLATE_PATH = '{root_dir}/templates/dell_vlan.j2'.format(root_dir=ROOT_DIR)
QUANTA_INTERFACE_TEMPLATE_PATH = '{root_dir}/templates/quanta_interface.j2'.format(root_dir=ROOT_DIR)
QUANTA_VLAN_TEMPLATE_PATH = '{root_dir}/templates/quanta_vlan.j2'.format(root_dir=ROOT_DIR)
GENERATED_CONFIG_FILE_PATH = '{root_dir}/generated_config.txt'.format(root_dir=ROOT_DIR)
TOOL_VERSION = '1.2'
LAST_UPDATE = '09.07.2020'


def split_vlans(vlans):
    vlan_list = []

    vlans = vlans.replace(' ', '')
    splitted_by_coma = vlans.split(',')

    for splitted in splitted_by_coma:
        if '-' in splitted:
            vlan_range = splitted.split('-')

            if len(vlan_range) != 2 or int(vlan_range[0]) > int(vlan_range[1]):
                raise ValueError('Vlan range {vlan_range} is not correct'.format(vlan_range=vlan_range))

            for vlan in range(int(vlan_range[0]), int(vlan_range[1]) + 1):
                vlan_list.append(vlan)
        else:
            int(splitted)
            vlan_list.append(splitted)

    for vlan in vlan_list:
        if not (4094 >= int(vlan) >= 1):
            raise ValueError('Vlan {vlan} is not correct'.format(vlan=vlan))

    return set(vlan_list)

class NetworkConfigGenerator:
    _csv_file_path = ROOT_DIR + '/config.csv'
    _loaded_config = []
    _generated_configs = ''
    _csv_columns = ['Interface', 'Description', 'Vlan', 'Switchport type', 'Vendor', 'Default interface',
                    'Switchport command', 'Initialize vlans']

    def __init__(self):
        banner = ['********************************************************************************\n',
                  'Thanks for using NetworkConfigGenerator by Radoslaw Kochman',
                  'Current version: {version}, last update: {last_update}\n'.format(version=TOOL_VERSION,last_update=LAST_UPDATE),
                  'For more information about the tool, please visit https://garzum.net/\n',
                  'Latest version can be downloaded from git repository at',
                  'https://gitlab.com/garzum/networkconfiggenerator\n',
                  'Currently supported platforms:',
                  '* Cisco',
                  '* Dell FTOS 9',
                  '* Quanta\n',
                  '********************************************************************************\n']

        for line in banner:
            print('{: ^80s}'.format(line))

        self._load_templates()
        loaded_config = self._load_csv()
        self._generate_config(loaded_config)
        self._save_config_to_file()
        input('Press enter to exit...')

    def _load_templates(self):
        with open(CISCO_INTERFACE_TEMPLATE_PATH) as f:
            self._cisco_interface_template = Template(f.read(), keep_trailing_newline=True)
        with open(CISCO_VLAN_TEMPLATE_PATH) as f:
            self._cisco_vlan_template = Template(f.read(), keep_trailing_newline=True)
        with open(DELL_INTERFACE_TEMPLATE_PATH) as f:
            self._dell_interface_template = Template(f.read(), keep_trailing_newline=True)
        with open(DELL_VLAN_TEMPLATE_PATH) as f:
            self._dell_vlan_template = Template(f.read(), keep_trailing_newline=True)
        with open(QUANTA_INTERFACE_TEMPLATE_PATH) as f:
            self._quanta_interface_template = Template(f.read(), keep_trailing_newline=True)
        with open(QUANTA_VLAN_TEMPLATE_PATH) as f:
            self._quanta_vlan_template = Template(f.read(), keep_trailing_newline=True)

    def _load_csv(self):
        try:
            with open(self._csv_file_path, mode='r') as f:
                reader = csv.DictReader(f,delimiter=';')

                for column in self._csv_columns:
                    if column not in reader.fieldnames:
                        print('Error: Column {column} not found in the config.csv file, '
                              'please reefer to the example. Exiting.'.format(column=column))
                        input('Press enter to exit...')
                        exit(1)

                return list(reader)
        except FileNotFoundError:
            print('Error: config.csv file not found in project directory.')
            input('Press enter to exit...')
            exit(1)

    def _generate_config(self, loaded_config):
        if len(loaded_config) == 0:
            print('Config is not present in the config.csv file, exiting.')
            input('Press enter to exit...')
            exit(1)

        row_number = 1
        for row in loaded_config:
            row_number += 1
            if not row['Interface']:
                print('Warning: Interface name not found in row {row_number}, skipping.'
                      '\n{row_values}'.format(row_number=row_number, row_values=row))
                continue
            if not row['Switchport type'] or (row['Switchport type'].lower() != 'access' and row['Switchport type'].lower() != 'trunk'):
                print('Warning: Incorrect switchport type in row {row_number}, '
                      'available values: access/trunk. skipping.\n{row_values}'
                      ''.format(row_number=row_number, row_values=row))
                continue

            if not row['Vlan']:
                print('Warning: Vlan not found in row {row_number}, skipping.'
                      '\n{row_values}'.format(row_number=row_number, row_values=row))
                continue

            if row['Switchport type'].lower() == 'access':
                try:
                    if not 4094 >= int(row['Vlan']) >= 1:
                        raise ValueError()
                except Exception:
                    print('Warning: Vlan value is incorrect in row {row_number}, skipping.'
                          '\n{row_values}'.format(row_number=row_number, row_values=row))
                    continue

            if row['Switchport type'].lower() == 'trunk':
                try:
                    split_vlans(row['Vlan'])
                except Exception:
                    print('Warning: Vlan value is incorrect in row {row_number}, skipping.'
                          '\n{row_values}'.format(row_number=row_number, row_values=row))
                    continue

            if not row['Vendor']:
                print('Warning: Incorrect vendor in row {row_number}, '
                      'available values: cisco/dell/quanta. skipping.\n{row_values}'
                      ''.format(row_number=row_number, row_values=row))
                continue
            elif row['Vendor'] == 'cisco':

                interface_config = self._cisco_interface_template.render(
                    interface=row['Interface'],
                    description=row['Description'],
                    vlan=row['Vlan'],
                    switchport_type=row['Switchport type'],
                    default_interface=row['Default interface'],
                    switchport_command=row['Switchport command']
                )

                if row['Initialize vlans'] == 'y':
                    try:
                        for vlan in split_vlans(row['Vlan']):
                            interface_config += self._cisco_vlan_template.render(
                                vlan=vlan
                            )
                    except ValueError:
                        print('Warning: Incorrect vlan value found in row {row_number}, skipping.'
                              '\n{row_values}'.format(row_number=row_number, row_values=row))
                        continue

            elif row['Vendor'] == 'dell':
                interface_config = self._dell_interface_template.render(
                    interface=row['Interface'],
                    description=row['Description'],
                    default_interface=row['Default interface'],
                    switchport_command=row['Switchport command']
                )

                try:
                    for vlan in split_vlans(row['Vlan']):
                        interface_config += self._dell_vlan_template.render(
                            interface=row['Interface'],
                            vlan=vlan,
                            switchport_type=row['Switchport type']
                        )
                except ValueError:
                    print('Warning: Incorrect vlan value found in row {row_number}, skipping.'
                          '\n{row_values}'.format(row_number=row_number, row_values=row))
                    continue

            elif row['Vendor'] == 'quanta':
                interface_config = self._quanta_interface_template.render(
                    interface=row['Interface'],
                    description=row['Description'],
                    vlan=row['Vlan'],
                    switchport_type=row['Switchport type'],
                    switchport_command=row['Switchport command']
                )

                if row['Initialize vlans'] == 'y':
                    try:
                        interface_config += 'vlan database\n'
                        for vlan in split_vlans(row['Vlan']):
                            interface_config += self._quanta_vlan_template.render(
                                vlan=vlan
                            )
                        interface_config += 'exit\n'
                    except ValueError:
                        print('Warning: Incorrect vlan value found in row {row_number}, skipping.'
                              '\n{row_values}'.format(row_number=row_number, row_values=row))
                        continue
            else:
                print('Warning: Vendor not recognised in row {row_number}, '
                      'available values: cisco/dell/quanta. skipping.\n'
                      '{row_values}'.format(row_number=row_number, row_values=row))
                continue

            self._generated_configs += interface_config

        if self._generated_configs:
            print('\nGenerated config:\n{generated_configs}'.format(generated_configs=self._generated_configs))
        else:
            print('\nNo config was generated, please check configuration file.')

    def _save_config_to_file(self):
        if self._generated_configs:
            with open(GENERATED_CONFIG_FILE_PATH, 'w') as f:
                f.write(self._generated_configs)
            print('Generated config saved to {config_path}'.format(config_path=GENERATED_CONFIG_FILE_PATH))


generator = NetworkConfigGenerator()
