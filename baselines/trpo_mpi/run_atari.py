#!/usr/bin/env python3
import os

from mpi4py import MPI

from baselines.common import set_global_seeds
from baselines import bench, logger
from baselines.common.atari_wrappers import make_atari, wrap_deepmind
from baselines.common.cmd_util import atari_arg_parser
from baselines.trpo_mpi.nosharing_cnn_policy import CnnPolicy
from baselines.trpo_mpi import trpo_mpi


def train(env_id, num_timesteps, seed):
    rank = MPI.COMM_WORLD.Get_rank()

    if rank == 0:
        logger.configure()
    else:
        logger.configure(format_strs=[])

    workerseed = seed + 10000 * MPI.COMM_WORLD.Get_rank()
    set_global_seeds(workerseed)
    env = make_atari(env_id)

    def policy_fn(name, ob_space, ac_space, sess=None):  # pylint: disable=W0613
        return CnnPolicy(name=name, ob_space=ob_space, ac_space=ac_space, sess=sess)

    env = bench.Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)))
    env.seed(workerseed)

    env = wrap_deepmind(env)
    env.seed(workerseed)

    trpo_mpi.learn(env, policy_fn, timesteps_per_batch=512, max_kl=0.001, cg_iters=10, cg_damping=1e-3,
                   max_timesteps=int(num_timesteps * 1.1), gamma=0.98, lam=1.0, vf_iters=3, vf_stepsize=1e-4,
                   entcoeff=0.00)
    env.close()


def main():
    args = atari_arg_parser().parse_args()
    train(args.env, num_timesteps=args.num_timesteps, seed=args.seed)


if __name__ == "__main__":
    main()
