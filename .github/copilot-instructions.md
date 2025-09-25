> No. This is garbage and it came in too late. I asked for early pull requests because I'm traveling, and if you can't
> follow that rule, at least make the pull requests *good*.
>
> This adds various garbage that isn't RISC-V specific to generic header files.
>
> And by "garbage" I really mean it. This is stuff that nobody should ever send me, never mind late in a merge window.
>
> Like this crazy and pointless make_u32_from_two_u16() "helper".
>
> That thing makes the world actively a worse place to live. It's useless garbage that makes any user incomprehensible,
> and actively *WORSE* than not using that stupid "helper".
>
> If you write the code out as "(a << 16) + b", you know what it does and which is the high word. Maybe you need to add
> a cast to make sure that 'b' doesn't have high bits that pollutes the end result, so maybe it's not going to be exactly
_pretty_, but it's not going to be wrong and incomprehensible either.
>
> In contrast, if you write make_u32_from_two_u16(a,b) you have not a f%^5ing clue what the word order is. IOW, you just
> made things *WORSE*, and you added that "helper" to a generic non-RISC-V file where people are apparently supposed to
> use it to make *other* code worse too.
>
> So no. Things like this need to get bent. It does not go into generic header files, and it damn well does not happen
> late in the merge window.
>
> You're on notice: no more late pull requests, and no more garbage outside the RISC-V tree.
>
> Now, I would *hope* there's no garbage inside the RISC-V parts, but that's your choice. But things in generic headers
> do not get polluted by crazy stuff. And sending a big pull request the day before the merge window closes in the hope
> that I'm too busy to care is not a winning strategy.
>
> So you get to try again in 6.18. EARLY in the that merge window. And without the garbage.
>
> -- Linus Torvalds on Helper Functions

^^ This is what should not be done. Period.
