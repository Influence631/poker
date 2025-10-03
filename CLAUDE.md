<- scan all the project related files.

issues:
1. when starting the match, the bot 0 and 1 (or sm and bb) shouldnt be blindfoldenly calling in 0s, they should take a bit of time.

2. upon dealing community cards, the animation of bots actions is skipped because of the label "deling flop, turn, etc" -> when the cards are dealt, the bots shouldnt make moves until the label is gone. and the labels should be gone a bit quicker.

3. the behaviour of the bots is incredibly stupid. make it more clever for each level. you may create an .env file for a anthropic api key, so that the bots actually have proper evaluation based promts, based of the difficulty level. the .env should not be in the git.

also, explain to me in details the flow of the game, cause it seems like there are some inconsistancies in the order of turns as the game goes.
