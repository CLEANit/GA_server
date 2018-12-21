#!/bin/bash
ssh fock squeue -u $1 | wc -l
