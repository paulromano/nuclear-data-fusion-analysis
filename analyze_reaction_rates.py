import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('json_file')
parser.add_argument('output_suffix')
args = parser.parse_args()


with open(args.json_file, 'r') as fh:
    rates = json.load(fh)

endfb80_rates = rates['endfb-viii.0']
endfb81_rates = rates['endfb-viii.1']
fendl32_rates = rates['fendl-3.2b']

# Determine full set of nuclides / reactions
nuclides = set()
reactions = set()
for lib_rates in rates.values():
    nuclides |= lib_rates.keys()
    for d in lib_rates.values():
        reactions |= d.keys()

simple_name = {
    '(n,elastic)': 'elastic',
    '(n,gamma)': 'capture',
    '(n,p)': 'np',
    '(n,d)': 'nd',
    '(n,t)': 'nt',
    '(n,3He)': 'n3He',
    '(n,a)': 'na',
    '(n,Xp)': 'proton_prod',
    '(n,Xd)': 'deuteron_prod',
    '(n,Xt)': 'triton_prod',
    '(n,X3He)': 'helium3_prod',
    '(n,Xa)': 'alpha_prod',
    'heating': 'heating',
    'damage-energy': 'damage',
}

# Create directory for HTML files
Path('reports').mkdir(exist_ok=True)

dataframes = {}
for reaction in reactions:
    records = []
    for nuclide in sorted(nuclides):
        e80 = endfb80_rates[nuclide].get(reaction)
        e81 = endfb81_rates[nuclide].get(reaction)
        f32 = fendl32_rates[nuclide].get(reaction)
        if e80 is not None and e81 is not None and f32 is not None:
            ratio_81_to_80 = e81/e80 if e80 != 0.0 else np.nan
            ratio_80_to_f = e80/f32 if f32 != 0.0 else np.nan
            ratio_81_to_f = e81/f32 if f32 != 0.0 else np.nan
            records.append((nuclide, ratio_81_to_80, ratio_80_to_f, ratio_81_to_f))
    dataframes[reaction] = df = pd.DataFrame.from_records(
        records, columns=['Nuclide', 'E81/E80', 'E80/F32', 'E81/F32'], index='Nuclide')

    name = simple_name[reaction]
    df.style \
        .format(precision=3) \
        .background_gradient(axis=None, vmin=0.5, vmax=1.5, cmap='RdBu_r') \
        .to_html(f'reports/{name}_{args.output_suffix}.html')
