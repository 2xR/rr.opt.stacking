from __future__ import unicode_literals
from opt.solver import Solver
from utils.gauge import Gauge
from utils.misc import INF

from stacking.solvers.treenode import SP_TreeNode
from stacking.instance import Instance


class SP_SG(Solver):
    instance_loader = staticmethod(Instance.load)

    def __init__(self, log=None):
        self.iterations = Gauge(0)     # main loop iteration counter
        self.improvements = Gauge(0)   # upper bound improvement counter
        Solver.__init__(self, log)
        # register solver limits
        self.limits.register("iterations", self.iterations)
        self.limits.register("improvements", self.improvements)
        # register solver stop conditions
        iteration_limit_reached = lambda: self.iterations.remaining <= 0
        self.stops.register("iterations", iteration_limit_reached, value=Solver.ACTION.PAUSE,
                            priority=0, message="Iteration limit reached.", auto_check=True)

        improvement_limit_reached = lambda: self.improvements.remaining <= 0
        self.stops.register("improvements", improvement_limit_reached, value=Solver.ACTION.PAUSE,
                            priority=0, message="Improvement limit reached.", auto_check=False)

    def step(self):
        node = SP_TreeNode.root(self)
        node.semi_greedy_complete(cut=self.upper_bound)
        z = node.objective()
        if z < self.upper_bound:
            sol_data, sol_meta = node.solution_and_meta()
            self.solutions.add(sol_data, objective=z, **sol_meta)
        self.iterations += 1

    @Solver.uninitialized.on_enter
    def uninitialized(self):
        Solver.uninitialized.enter(self)
        self.iterations.clear()
        self.improvements.clear()

    @Solver.initialized.on_enter
    def initialized(self, instance, cpu=INF, iterations=INF, improvements=INF,
                    seed=None, **params):
        Solver.initialized.enter(self, instance, seed=seed, **params)
        self.limits.set(cpu=cpu, iterations=iterations, improvements=improvements)

    @Solver.running.on_enter
    def running(self, cpu=None, iterations=None, improvements=None):
        self.limits.set(cpu=cpu, iterations=iterations, improvements=improvements)
        self.limits.report(ostream=self.log.info)
        self.stops.clear()
        RUNNING = Solver.STATE.RUNNING
        with self.cpu.tracking():
            try:
                while self.state == RUNNING and not self.stops.check():
                    self.step()
            except KeyboardInterrupt:
                self.stops.add("Keyboard interrupt.", value=Solver.ACTION.PAUSE, priority=0)
            if self.state == RUNNING:
                self.input(self.stops.value)
        return self.solutions.best()

    def set_upper_bound(self, ub):
        old_ub = self.upper_bound
        Solver.set_upper_bound(self, ub)
        if ub < old_ub:
            self.improvements += 1
            self.stops.check("improvements")


sg = SP_SG()
if __name__ == "__main__":
    exit(sg.cli())
