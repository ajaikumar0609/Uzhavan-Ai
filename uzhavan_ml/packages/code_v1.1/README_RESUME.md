# M4 training code v1.1: epoch-level resume

The training protocol is unchanged from v1.0: data, split, classes, EfficientNetV2-S, bs 32, 30 epochs, AdamW + cosine, augmentation, loss and early stopping (the config hash is identical). Only checkpointing and resume changed.

- `checkpoint_last.pt` is written atomically (tmp + os.replace) after every completed epoch. It contains the model, optimizer, scheduler and AMP-scaler states, the last completed epoch, the best val macro-F1, the early-stopping counter, the full history, the seed, the classes, the config and the RNG states.
- `history.json` and `experiment.json` (status running/interrupted/failed/completed, last_completed_epoch, best F1, start and last-checkpoint time, hardware) are also written atomically every epoch.
- `--resume auto` (the default) resumes from `<out>/UZ-M4-v1.0-<confighash>-s<seed>/checkpoint_last.pt` inside the same folder. `--resume PATH` resumes a specific checkpoint. `--resume none` refuses to overwrite an existing checkpoint.
- A completed experiment is never overwritten. SIGTERM or Ctrl-C marks the run `interrupted` and prints the resume command.
- Local tests (`test_m4_resume.py`): 21/21 pass, including an interrupted+resumed run whose metrics are identical to an uninterrupted run.
