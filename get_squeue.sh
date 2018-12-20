#!/bin/bash
ssh fock squeue -u $1 -t PD | wc -l
