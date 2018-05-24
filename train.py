# coding=utf8
import sys
import time

from config_default import *
import utils
from utils import Task

class Trainer(object):
    def __init__(self, task):
        self.task = task

        self.N_EPOCHS = task.config['train']['n_epochs']
        self.model = task.model
        self.optimizer = task.optimizer
        self.loss_func = task.loss_func
        self.epoch = task.epoch
        self.train_loader = task.train_loader
        self.valid_loader = task.valid_loader
        utils.printf_EVERY = task.config['train']['print_every']
    
    def train(self):
        utils.printf('Training Start ...')
        self.model.train()
        start_time = time.time()
        for epoch in range(self.epoch, self.N_EPOCHS):
            self.train_loader.shuffle() # 更换batch顺序
            total_loss = 0
            last_time = time.time()
            utils.printf(f'\nEpoch {epoch+1:5d}/{self.N_EPOCHS:5d}:')
            for i, batch in enumerate(self.train_loader):
                src_var, tgt_var, src_lens, tgt_lens = batch

                self.model.zero_grad()
                outputs, hidden = self.model(src_var, tgt_var[:-1], src_lens)

                loss = self.loss_func(outputs, tgt_var[1:].contiguous(), tgt_lens)
                total_loss += loss.data[0]
                self.optimizer.step()

                if (i + 1) % utils.printf_EVERY == 0:
                    mean_ppl = utils.PPL(total_loss / print_every)
                    utils.printf(f'\tBatch {i+1:5d}/{self.N_EPOCHS:5d}; Train PPL: {mean_ppl: 6.2f}; {time.time() - last_time:6.0f} s elapsed')
                    total_loss = 0
                    last_time = time.time()
                 
            self.validate()
            

    def validate(self):
        self.model.eval()
        loss_total = 0
        for i, batch in enumerate(self.valid_loader):
            src_var, tgt_var, src_lens, tgt_lens = batch

            outputs, hidden = self.model(src_var, tgt_var[:-1], src_lens)
            loss = self.loss_func(outputs, tgt_var[1:].contiguous(), tgt_lens)
            loss_total += loss.data[0]
        self.model.train()
        ppl = utils.PPL(loss_total / len(self.valid_loader))
        utils.printf(f'\tValid PPL: {ppl: 6.2f}\n')



if __name__ == '__main__':
    task = Task(config)
    if len(sys.argv) > 2:
        # load checkpoint
        task.load(mode='train', model_path=sys.argv[1])
    else:
        # 重新训练
        if config['train']['silence']:
            # backgrounder
            sys.stdout = open('train.log', 'w')
        task.load(mode='train')
    trainer = Trainer(task)
    trainer.train()
