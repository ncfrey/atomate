from fireworks import Firework, Workflow
from matmethods.vasp.firetasks.parse_outputs import VaspToDBTask
from matmethods.vasp.firetasks.run_calc import RunVaspDirect
from matmethods.vasp.firetasks.tests.vasp_fake import RunVaspFake
from matmethods.vasp.firetasks.write_inputs import WriteVaspFromIOSet
from pymatgen import Lattice, IStructure

__author__ = 'Anubhav Jain <ajain@lbl.gov>'


def get_basic_workflow(structure, vasp_input_set="MPVaspInputSet", vasp_cmd="vasp"):

    write_task = WriteVaspFromIOSet(structure=structure, vasp_input_set=vasp_input_set)
    run_task = RunVaspDirect(vasp_cmd=vasp_cmd)
    parse_task = VaspToDBTask()

    my_fw = Firework([write_task, run_task, parse_task])

    return Workflow.from_Firework(my_fw)


def get_basic_workflow_fake(structure, vasp_input_set="MPVaspInputSet", fake_dir=None):

    my_wf = get_basic_workflow(structure, vasp_input_set)

    # replace original Run Vasp task with fake task
    wf_dict = my_wf.to_dict()
    wf_dict["fws"][0]["spec"]["_tasks"][1] = RunVaspFake(fake_dir=fake_dir).to_dict()

    return Workflow.from_dict(wf_dict)




if __name__ == "__main__":
    coords = [[0, 0, 0], [0.75, 0.5, 0.75]]
    lattice = Lattice([[3.8401979337, 0.00, 0.00],
                                [1.9200989668, 3.3257101909, 0.00],
                                [0.00, -2.2171384943, 3.1355090603]])
    structure = IStructure(lattice, ["Si"] * 2, coords)

    print get_basic_workflow(structure).to_dict()