import argparse
import openmc
import openmc.lib
import numpy as np
from pathlib import Path
import json


parser = argparse.ArgumentParser()
parser.add_argument('flux_file')
args = parser.parse_args()

# Read spectrum data from file
data = np.loadtxt(args.flux_file, skiprows=2, max_rows=616)
group = data[:, 0]
upper = data[:, 1]
lower = data[:, 2]
lethargy = data[:, 3]
flux = data[:, 4]
flux_per_lethargy = data[:, 5]

# Put energies into a single monotonically increasing array
energies = np.hstack((lower[::-1], upper[:1]))

# Reverse fluxes to match energies
flux = flux[::-1].copy()

# Get list of nuclides from FENDL 3.2b
files = sorted(Path('/opt/data/hdf5/fendl-3.2b-hdf5/neutron').glob('*.h5'))
nuclides = [f.stem for f in files]

# Create dummy OpenMC model with a single nuclide to load
m = openmc.Material()
m.add_nuclide('H1', 1.0)
model = openmc.Model()
model.geometry = openmc.Geometry([openmc.Cell(fill=m, region=-openmc.Sphere(boundary_type='vacuum'))])
model.settings.particles = 1000
model.settings.batches = 10
model.settings.run_mode = 'fixed source'
model.export_to_model_xml()

# Define reactions of interest
reactions = {
    2,
    102,
    103,
    104,
    105,
    106,
    107,
    203, # p production
    204, # d production
    205, # t production
    206, # 3he production
    207, # alpha production
    301, # heating
    444, # damage
}

def get_collapsed_rates(datadir):
    # Set cross section library
    openmc.config['cross_sections'] = f'{datadir}/cross_sections.xml'

    # Initiailize OpenMC
    openmc.lib.init(output=False)

    rates = {}
    for nuclide in nuclides:
        # Determine reactions that are available
        rates[nuclide] = {}
        h5_nuc = openmc.data.IncidentNeutron.from_hdf5(f'{datadir}/neutron/{nuclide}.h5')
        reactions_available = {int(x) for x in h5_nuc.reactions.keys()}

        # Only look at available reactions that are of interest
        mts = reactions_available & reactions

        # Load nuclide data in OpenMC
        openmc.lib.load_nuclide(nuclide)
        nuc = openmc.lib.nuclides[nuclide]

        # For each reaction, collapse the flux with the cross section
        for mt in mts:
            rxname = openmc.data.REACTION_NAME[mt]
            rates[nuclide][rxname] = nuc.collapse_rate(mt, 293.6, energies, flux)

    # Finalize OpenMC and return rates
    openmc.lib.finalize()
    return rates

rates = {}
rates['endfb-viii.0'] = get_collapsed_rates('/opt/data/hdf5/endfb-viii.0-hdf5')
rates['endfb-viii.1'] = get_collapsed_rates('/opt/data/hdf5/endfb-viii.1-hdf5')
rates['fendl-3.2b'] = get_collapsed_rates('/opt/data/hdf5/fendl-3.2-hdf5')

# Write out rates to a JSON file
with open('reaction_rates.json', 'w') as fh:
    json.dump(rates, fh)
