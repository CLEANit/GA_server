# GA_server

This repository contains code for running a Genetic Algoritm (GA) server with workers based on MongoDB for communicating policy seeds.

- The server (or conductor) code generates/loads the initial population, sorts population by average score, performs mutation opterations, and monitors the status of policies.
- The worker code generates the network-based policy from the random seeds and evaluates them on the desired environment.
