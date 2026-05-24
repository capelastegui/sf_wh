# Introduction

This document explains combat concepts in wh40k. In particular, it explains how attacks work.

# Basic concepts

This is a turn based 2 player game. There are 5 rounds per game, and every round, each player takes a turn.

Each player controls an army made of units, which are deployed on the game board and can move, attack or perform other actions. Each unit is composed of one or more models. 

# Attack sequence basics

Each model in a unit has one or more wounds. Attacks cause damage which reduce model wounds, and models dropping to 0 wounds are killed. Once all models in a unit are killed, the unit is destroyed.

Attacks are resolved as follows:
- Select attacker and targets
  - Choose one attacking unit
  - Determine which of the units' weapons will be used to attack
  - For each weapon, select a valid target
- For each attacking weapon
  - Determine number of *attacks*
  - Roll to hit: This determines number of *hits*
    - (optional): Some of these hits may be *critical hits*
  - Roll to wound: This determines number of *wounds*
    - (optional): Some of these wounds may be *critical wounds*
  - In sequence:
    - Allocate attack to a model
    - Roll to save: This may result in an *unsaved attack*
    - Roll damage: This determines amount of *damage*
      - (optional) Roll Feel No Pain: This may reduce amount of *damage*
      - Note: damage exceeding remaining model wounds is ignored. Sometimes it is useful to calculate total damage before applying this cap - we call this *uncapped damage*
    - Remove models: If damage exceeds remaining model wounds, the model is *killed*
      - The number of models killed in an attack cannot exceed the number of remaining models in the target unit. However, it is often useful to estimate a number of killed models as if this limit didn't exist.

The sequence can be summarised as:
- round -> attacks -> hits -> wounds -> n * (unsaved attack -> damage -> kill)

Combat Sequence Abbreviations:
- R: round
- A: attack
- H: hit
  - CH: critical hit
  - NH: non-critical hit
- W: wound
  - CW: critical wound
  - NW: non-critical wound
- UA: unsaved attack
- D: damage
- UD: uncapped damage
- K: kills

In this project, we provide a series of tools to calculate or predict combat outcomes. The main metrics we use are:
- kills per round: Number of models killed by a set of attacking weapons, in a round
- rounds to kill: Number of rounds it takes to kill a model or unit with a set of attacking weapons

These are often abbreviated as KpR and RtK. More generally we sometimes want to estimate the ratio between any 2 steps X, Y in a combat sequence (where Y comes after X):
- YpX: Y per X: Value of Y for each X
- XtY: X to Y: Number of X it takes to get a unit of Y


Examples:
- KpA: Kills per attack
- HtW: Hits to wound


Unless we say otherwise, when we talk about these metrics we refer to average values.


# Application

The two main uses of these concepts are:
- To resolve combat outcomes in a game: If unit A attacks unit B, how many models are killed?
- To analyse game elements: How useful is weapon A against targets X and Y? How does it compare to weapon B?

Usually, we will focus on the analysis aspect.
