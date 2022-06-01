# Super Alpha Pet

## Super Auto Pet playing AI

## Components
 - Reinforcement Learning
 - Animal/Food database
 - Battle Simulator
 - Training Dataset ? 
 - Game-overlay with AI-suggested moves

## Tasks
 - [ ] Simulate game in python
 - [ ] Build battle function
 - [ ] Team/Animal/Food classes
 - [ ] 

## How to train (workflow)
 - model (AI) do action
 - evaluate AI choice
   - That rewards short/long-term success
 - learn 

## Example (Turn 1 AI)
 - AI given N different Turn 1 shops
 - AI chooses N teams
 - N teams battle each other
 - each AI gets their winrate
 - model shifts/learns

## Tree search model-type-thing
 - Given a shop
 - choice 1
   - choice 2 
    - choice 3
   - choice 2 
    - choice 3
    - etc.
 - After tree search, model looks at all the teams it could make
 - picks what the model thinks is the best one, then does that series of choices
   - C: rolls?
   - C: random food/animal effects?
   - P: check all animal placements
   - P: Evaluate right away

Dev on Windows: Virtual python environment
 - C:\Users\songw\superalphapet
 - Python 3.7.9
 - Need to uninstall previous versions of NVIDIA CUDA (via Control Panel)
 - Pytorch on Windows only supporting cuda 11.3


