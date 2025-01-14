import os
import datetime
import torch


class CheckpointHandler:
    def __init__(self):
        self.prefix_name = "checkpoint"

    def store_var(self, var_name, value, exist_fail=False):
        if exist_fail is True and hasattr(self, var_name):
            raise Exception("var_name='{}' already exists".format(var_name))
        else:
            setattr(self, var_name, value)

    def get_var(self, var_name):
        if hasattr(self, var_name):
            value = getattr(self, var_name)
            return value
        else:
            return False

    def store_running_var(self, var_name, iteration, value):
        if hasattr(self, var_name):
            cur = getattr(self, var_name)
            cur[iteration] = value
            setattr(self, var_name, cur)
        else:
            setattr(self, var_name, {iteration: value})

    def get_running_var(self, var_name, iteration=None):
        if hasattr(self, var_name):
            if iteration == None:
                return getattr(self, var_name)
            else:
                cur = getattr(self, var_name)
                value = cur.get(iteration, None)
                if value is None:
                    return False
                else:
                    return value
        else:
            return False

    def store_running_var_with_header(self, header, var_name, iteration, value):
        if hasattr(self, header):
            cur_header = getattr(self, header)
            if var_name in cur_header:
                cur_header[var_name][iteration] = value
            else:
                cur_header[var_name] = {iteration: value}
            setattr(self, header, cur_header)
        else:
            setattr(self, header, {var_name: {iteration: value}})

    def get_running_var_with_header(self, header, var_name, iteration):
        if hasattr(self, header):
            cur_header = getattr(self, header)
            if var_name in cur_header:
                value = cur_header[var_name].get(iteration, None)
                if value is None:
                    return False
                else:
                    return value
            else:
                return False
        else:
            return False

    def generate_checkpoint_path(self, path2save):
        now = datetime.datetime.now()
        filename = self.prefix_name + "_" + now.strftime("D%d_%m_%Y_T%H_%M") + ".pth.tar"
        checkpoint_path = os.path.join(path2save, filename)
        return checkpoint_path

    def save_checkpoint(
        self, checkpoint_path, iteration, batch_count, model, optimizer, scheduler=None
    ):
        if type(model) == torch.nn.DataParallel:
            # converting a DataParallel model to be able load later without DataParallel
            self.model_state_dict = model.module.state_dict()
        else:
            self.model_state_dict = model.state_dict()

        self.optimizer_state_dict = optimizer.state_dict()
        if scheduler is not None:
            self.scheduler_state_dict = scheduler.state_dict()
        else:
            self.scheduler_state_dict = None

        self.iteration = iteration
        self.batch_count = batch_count
        torch.save(self, checkpoint_path)

    @staticmethod
    def load_checkpoint(checkpoint_path, map_location="cpu"):
        checkpoint = torch.load(checkpoint_path, map_location=map_location)
        return checkpoint

    @staticmethod
    def load_checkpoint_with_model(
        checkpoint_path, model=None, optimizer=None, scheduler=None, map_location="cpu"
    ):
        checkpoint = torch.load(checkpoint_path, map_location=map_location)
        if model is not None:
            model.load_state_dict(checkpoint.model_state_dict)
        if optimizer is not None:
            optimizer.load_state_dict(checkpoint.optimizer_state_dict)
        if scheduler is not None:
            if checkpoint.scheduler_state_dict is not None:
                scheduler.load_state_dict(checkpoint.scheduler_state_dict)
            else:
                raise Exception("Non scheduler state dict available")
        return checkpoint, model, optimizer, scheduler
