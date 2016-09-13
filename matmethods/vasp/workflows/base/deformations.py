# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

"""
This module defines the deformation workflow: structure optimization followed by transmuter fireworks.
"""

from fireworks import Workflow

from matmethods.utils.utils import get_logger
from matmethods.vasp.firetasks.glue_tasks import PassStressStrainData
from matmethods.vasp.fireworks.core import OptimizeFW, TransmuterFW

from pymatgen.io.vasp.sets import MPRelaxSet, MPStaticSet

__author__ = 'Kiran Mathew'
__credits__ = "Joseph Montoya"
__email__ = 'kmathew@lbl.gov'

logger = get_logger(__name__)


def get_wf_deformations(structure, deformations, name="elastic deformation", vasp_input_set=None,
                        lepsilon=False, vasp_cmd="vasp", db_file=None, user_kpoints_settings=None,
                        pass_stress_strain=False, tag=""):
    """
    Returns a deforamtion workflow.

    Firework 1 : write vasp input set for structural relaxation,
                 run vasp,
                 pass run location,
                 database insertion.

    Firework 2 - len(deformations): Deform the optimized structure and run static calculations.


    Args:
        structure (Structure): input structure to be optimized and run
        deformations (list of 3x3 array-likes): list of deformations
        name (str): some appropriate name for the transmuter fireworks.
        vasp_input_set (DictVaspInputSet): vasp input set.
        lepsilon (bool): whether or not compute static dielectric constant/normal modes
        vasp_cmd (str): command to run
        db_file (str): path to file containing the database credentials.
        user_kpoints_settings (dict): example: {"grid_density": 7000}
        pass_stress_strain (bool): if True, stress and strain will be parsed and passed on.
        tag (str): some unique string that will be appended to the names of the fireworks so that
            the data from those tagged fireworks can be queried later during the analysis.

    Returns:
        Workflow
    """

    vis_relax = vasp_input_set or MPRelaxSet(structure, force_gamma=True)
    if user_kpoints_settings:
        v = vis_relax.as_dict()
        v.update({"user_kpoints_settings": user_kpoints_settings})
        vis_relax = vis_relax.__class__.from_dict(v)
    vis_static = MPStaticSet(structure, force_gamma=True, lepsilon=lepsilon,
                             user_kpoints_settings=user_kpoints_settings,
                             user_incar_settings={"ISIF": 2, "ISTART": 1})
    for key in ["MAGMOM", "LDAUU", "LDAUJ", "LDAUL"]:
        vis_static.incar.pop(key, None)

    fws = []

    # Structure optimization firework
    fws.append(OptimizeFW(structure=structure, vasp_input_set=vis_relax, vasp_cmd=vasp_cmd,
                          db_file=db_file, name="{} structure optimization".format(tag)))

    # Deformation fireworks with the task to extract and pass stress-strain appended to it.
    for deformation in deformations:
        fw = TransmuterFW(name="{} {}".format(tag, name), structure=structure,
                          transformations=['DeformStructureTransformation'],
                          transformation_params=[{"deformation": deformation.tolist()}],
                          vasp_input_set=vis_static, copy_vasp_outputs=True, parents=fws[0],
                          vasp_cmd=vasp_cmd, db_file=db_file)
        if pass_stress_strain:
            fw.spec['_tasks'].append(PassStressStrainData(deformation=deformation.tolist()).to_dict())
        fws.append(fw)

    wfname = "{}:{}".format(structure.composition.reduced_formula, name)

    return Workflow(fws, name=wfname)
