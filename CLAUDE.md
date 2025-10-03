<- scan all the project files and get the understanding of the project.

i think some of the cards use wrong textures -> the jack of hearts at least uses the ace texture. make sure that all the textures are mapped correctly. also, make sure that the maths evaluation and the ai evaluation of your hand is done by calculating the pot odds and out odds - and displaying those withing their evaluation. also make sure that the evaluation doesnt overlay with anything else. put it in top right corner of the screen.
the pot odds are calculated by (pot + the amount needed to call)/the amount needed to call, thus giving you a value like 3.5:1 in the case of having 70 in the pot (afte the opponent bet 20), then it costs you 20 to win 70 is 70 to 20 pot odds or 3.5 : 1.
then calculate the number of out (assuming you dont have any knowledge of the opponent cards) - for e.g you have 10 outs, and its a flop -> you know 5 cards out of 52, leaving you with 47 unknown cards -> your odds against hitting are 37:10 or 3.7
then if the pot odds are higher than the odds against, you should call or bet, otherwise fold.

also explain to me how does the ai evaluation mechanism work, does it use any llms or local ai models?

issues:
2. make sure that the pot odds and pots against are re-evaluated and a new suggestion is display upon every new know card, e.g a turn is drawn, then a river.

3. after a certain point (at least on medium difficulty), all the bots just check rather than betting anything. they should follow the same procedure of evaluating their actions by the pot odds for them and their odds against hitting, and then make a decision based of that.

4. it seems like no matter what the bots have in terms of combinations, but if you just go in for enough money - they always fold, even if they may have a decent chance of winning. this shouldnt be the case (cause it happens even on hard difficulty).

5. in the second or third round (when the sm is moving around and the order sequence changes) it seems like something is off, and the player then doesnt have a change to make any action untill a flop(??)


also add a proper .gitinit so nothing extra gets pushed to git