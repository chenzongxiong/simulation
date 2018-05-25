import tkinter as tk
from tkinter import filedialog

import log as logging
from simulation import Simulation2

LOG = logging.getLogger(__name__)


class BaseFrame(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.createWidgets()

    def createWidgets(self):
        self._sim = None
        self.agentN_frame = AgentNFrame(self.master)
        self.agentD_frame = AgentDFrame(self.master)
        self.noise_frame = NoiseFrame(self.master)

        self.agentN_frame.pack(padx=25, pady=25)
        self.agentD_frame.pack(padx=25, pady=25)
        self.noise_frame.pack(padx=25, pady=25)

        self.apply_button = tk.Button(self, text="Apply", command=self.apply)
        self.quit_button = tk.Button(self,  text="QUIT", fg="red", command=self.master.destroy)
        self.save_button = tk.Button(self, text="Save", command=self.save_image)
        self.apply_button.pack(side="right", padx=5, pady=5, expand=True)
        self.quit_button.pack(side="right", expand=True)
        self.save_button.pack(side="bottom", expand=True)
        self.pack()

    def _create_label_entry_compounds(self, name):
        frame = tk.Frame(self)
        frame.pack(fill="x")
        label_name = "{}_label".format(name)
        entry_name = "{}_entry".format(name)
        label_text = "{}: ".format(name)

        label = tk.Label(frame, text=label_text, width=20)
        var = getattr(self, name)
        entry = tk.Entry(frame, textvariable=var)

        setattr(self, label_name, label)
        setattr(self, entry_name, entry)
        getattr(self, label_name).pack(side="left", expand=True, padx=10)
        getattr(self, entry_name).pack(side="right", expand=True)

    def apply(self):
        self.parameters = {}
        # AgentN parameters
        for k, v in self.agentN_frame.parameters.items():
            self.parameters[k] = v.get()
        # AgentD parameters
        for k, v in self.agentD_frame.parameters.items():
            self.parameters[k] = v.get()
        # Noise parameters
        for k, v in self.noise_frame.parameters.items():
            self.parameters[k] = v.get()

        LOG.info("Parameter from GUI is: {}".format(self.parameters))
        self._sim = Simulation2(**self.parameters)
        self._sim.simulate()
        self._sim.plot()
        self._sim.show_plot()

    def save_image(self):
        if not self._sim:
            return

        fname = filedialog.asksaveasfilename(title="save image...",
                                             filetypes=(("jpeg files", "*.jpeg"),
                                                        ("png files", "*.png"),
                                                        ("svg files", "*.svg"),
                                                        ("all files", "*.*")))
        self._sim.save_plot(fname)


class AgentNFrame(BaseFrame):
    def __init__(self, master=None):
        super(AgentNFrame, self).__init__(master=master)

    def createWidgets(self):
        self._load_parameters()
        self.name = tk.Label(self, text="Real AgentN Config.")
        self.name.pack(side="top")

        self._create_label_entry_compounds("lower_bound_of_delta")
        self._create_label_entry_compounds("upper_bound_of_delta")
        self._create_label_entry_compounds("C_delta")
        self._create_label_entry_compounds("k_delta")
        self._create_label_entry_compounds("theta_delta")
        self._create_label_entry_compounds("C0_delta")

        self._create_label_entry_compounds("C_alpha")
        self._create_label_entry_compounds("k_alpha")
        self._create_label_entry_compounds("theta_alpha")

    def _load_parameters(self):
        self.lower_bound_of_delta = tk.DoubleVar(self, value=0.0)
        self.upper_bound_of_delta = tk.DoubleVar(self, value=20.0)
        self.C_delta = tk.DoubleVar(self, value=20.0)
        self.k_delta = tk.DoubleVar(self, value=7.5)
        self.theta_delta = tk.DoubleVar(self, value=1.0)
        self.C0_delta = tk.DoubleVar(self, 2.0)
        self.C_alpha = tk.DoubleVar(self, 1.0)
        self.k_alpha = tk.DoubleVar(self, 2.0)
        self.theta_alpha = tk.DoubleVar(self, 2.0)

        self.parameters = {
            "lower_bound_of_delta": self.lower_bound_of_delta,
            "upper_bound_of_delta": self.upper_bound_of_delta,
            "C_delta": self.C_delta,
            "k_delta": self.k_delta,
            "theta_delta": self.theta_delta,
            "C0_delta": self.C0_delta,
            "C_alpha": self.C_alpha,
            "k_alpha": self.k_alpha,
            "theta_alpha": self.theta_alpha
        }


class AgentDFrame(BaseFrame):
    def __init__(self, master=None):
        super(AgentDFrame, self).__init__(master=master)

    def createWidgets(self):
        self._load_parameters()
        self.name = tk.Label(self, text="Real AgentD Config.")
        self.name.pack(side="top")
        self._create_label_entry_compounds("lower_bound_of_beta")
        self._create_label_entry_compounds("upper_bound_of_beta")
        self._create_label_entry_compounds("step_of_beta")
        self._create_label_entry_compounds("k_beta")
        self._create_label_entry_compounds("theta_beta")

    def _load_parameters(self):
        self.lower_bound_of_beta = tk.DoubleVar(self, value=0.0)
        self.upper_bound_of_beta = tk.DoubleVar(self, value=20.0)
        self.step_of_beta = tk.DoubleVar(self, value=0.5)
        self.k_beta = tk.DoubleVar(self, value=2.0)
        self.theta_beta = tk.DoubleVar(self, value=2.0)

        self.parameters = {
            "lower_bound_of_beta": self.lower_bound_of_beta,
            "upper_bound_of_beta": self.upper_bound_of_beta,
            "step_of_beta": self.step_of_beta,
            "k_beta": self.k_beta,
            "theta_beta": self.theta_beta
        }


class NoiseFrame(BaseFrame):
    def __init__(self, master=None):
        super(NoiseFrame, self).__init__(master=master)

    def createWidgets(self):
        self._load_parameters()
        self.name = tk.Label(self, text="Noise Config.")
        self.name.pack(side="top")

        self._create_label_entry_compounds("mu")
        self._create_label_entry_compounds("sigma")
        self._create_label_entry_compounds("number_of_transactions")

    def _load_parameters(self):
        self.mu = tk.DoubleVar(self, value=0.0)
        self.sigma = tk.DoubleVar(self, value=0.5)
        self.number_of_transactions = tk.IntVar(self, value=50)

        self.parameters = {
            "mu": self.mu,
            "sigma": self.sigma,
            "number_of_transactions": self.number_of_transactions
        }


if __name__ == "__main__":
    # http://zetcode.com/gui/tkinter/layout/
    root = tk.Tk()
    root.title("Simulation")
    app = BaseFrame(master=root)
    app.mainloop()
