Board Assembly Using JLCPCB
===

<h6 style="text-align:right"> <i class='fa fa-calendar'></i> 2020-10-29</h6>


![test run](img/blog/seg16_diffusor_test.gif)

This is a brief blog post about using JLCPCB to do board assembly.
Though the board design was done with [MeowCAD](https://meowcad.com/project?projectId=006b550f-e142-4a36-b113-f90155cf7723), the focus will be
on the process of board assembly through JLCPCB.

Note that I'm not affiliated with JLCPCB (or PCBWay) in any way.
This was my first time ordering boards for manufacture and the experience
was very satisfying, so I'm chronicling it in this blog post in the hopes
others get something useful out of it.

Motivation and Design
---

I wanted to make a large [sixteen segment display](https://en.wikipedia.org/wiki/Sixteen-segment_display) using RGB LEDs.
There was a project called [Klais-16](https://github.com/openKolibri/klais-16) which provides 16 segment displays for $10.
While the Klais-16 project is awesome, the boards were just a little smaller than I wanted and were single color.

The price, [$10-$15](https://openkolibri.com/seg/16/), was also on the high side.
For small quantities, the $10-$15 prices is phenomenal but I wanted to see how cheap it would be for larger quantities.

So I designed my own using WS2812b 5050 RGB LEDs:

![seg16 schematic](img/blog/2020-10-29-seg16-sch.jpg){ width=500px }

![seg16 board](img/blog/2020-10-29-seg16-brd.jpg){ width=500px }


The "5050" in the LED name refers to their size (5mmx5mm) and the `b` variant refers to the LED having four leads.

The WS2812b has a tiny microcontroller embedded in it and uses it's own one wire protocol for communication.
This makes it easy to chain as only power, ground and data need be wired.

After downloading the project from MeowCAD and verifying the Gerbers, I started the process of submitting to [JLCPCB](https://jlcpcb.com/).
Downloading the boards

---

One design consideration was what parts JLCPCB had on hand.
After some investigation on JLCPCB's [parts library](https://jlcpcb.com/parts), I found the WS2812b.
One reason for choosing that particular part was that it had only 4 leads and was one of the only parts
I could easily find and import into MeowCAD.

Parts chosen from the JLCPCB parts library, the WS2812b and the 100nF capacitor,  were used to create the BOM file.

Prepping for Manufacture
---

After the Gerber files were put into a ZIP archive and uploaded, I filled options relating to size.
For some reason the board dimensions don't autofill so I used my best guess, which was 105mm x 135mm,
erring on the size of slightly larger.

![upload gerber](img/blog/blog-2020-10-29-jlcpcb-upload-gerber.jpg){ width=500px }

Further down the page is an 'SMT Assembly' button.
I guess JLCPCB only allows a green soldermask and SMT assembly for quantity less than 30.
Assuming both of those conditions are met, you can hit the toggle button and choose the appropriate side to
place parts on.

![smt assembly choice](img/blog/blog-2020-10-29-jlcpcb-smt-choice.jpg){ width=500px }

Once saved, there will be a screen to upload the BOM and CPL files.
I generated the CPL file by filtering JSON board file and taking the center of appropriate parts.

Here's the `bash` incantation (a combination of `grep` and `jq`) to generate the CPL for this project:

```
echo 'Designator,Mid X,Mid Y,Layer,Rotation'

jq -c '.element[]' ../../export/json/board.json  | \
  grep -v -P '"track"|"drawsegment"' | \
  grep '"SMD"' | \
  jq -r '. | [.text[0].text, 25.4*.x/10000, 25.4*.y/10000, "Top",((( (.orientation | tonumber)/10 ) + 360) % 360) ] | @csv'
```

Note that this would need to change depending on your project, as the `SMD` `grep` line is pretty hacky.

Regardless, once the BOM and CPL files are uploaded, you can review the selected parts:

![review selected parts](img/blog/blog-2020-10-29-jlcpcb-select-parts.jpg){ width=500px }

And then review the SMT part placement:

![review part placement](img/blog/blog-2020-10-29-jlcpcb-bom-cpl-confirm.jpg){ width=500px }

Once I was satisfied with the placement, I continued with the order:

![order confirm](img/blog/blog-2020-10-29-jlcpcb-checkout.jpg){ width=500px }

This was for an order of 10 boards, fully assembled.

I find it astounding that the price is only $47.44 for 10 boards.
That's about $4.75 for a fully assembled board.

When they arrived, I soldered a header on one and put it through it's paces to test:

![test run](img/blog/seg16_diffusor_test.gif)


Closing Remarks
---

Though this post is basically a "how to navigate JLCPCB's web site", I hope it demystifies the
process.
I know I was intimidated as this was the first board I ordered, fully assembled, from a manufacturer.
The whole process was straight forward and cheap.
Even if I had a problem with my layout, $50 was an acceptable amount of money I was willing to risk
on the experiment.

To re-emphasize, a fully assembled 105mm x 135mm board cost $4.75 in quantity 10.
For quantity 30, I calculate about $3.75.
I'm blown away by how cheap it is.

I believe this is why the Klais-16 folks can get away with charging the low rate of $10-$15 for their boards.

For comparison, I asked a domestic fabrication house and they quoted $27 for the Klais-16,
or $0.20 per placed part.
Doing a brief spot-check on OSH Park, the 105mm x 135mm board would run about $125 for 3, or about
$40 per board.

The shipping time for the sixteen segment displays ordered from JLCPCB was about 2-4 weeks.

I think there's probably good reason to go through a domestic board fabrication, either for
assembly or for PCB manufacture, but going through a Chinese service like JLCPCB or PCBWay
is upwards of 10x cheaper for a 1x-2x decrease in shipping time, at least for this project.

This project was very simple, it amounted to nothing more than two unique components, the
WS2812b and a capacitor, so surely boards with higher complexity have other more subtle problems
to deal with.

I decided to use JLCPCB because their interface allowed me to easily choose the 'assembly' option.
I tried [PCBWay](https://www.pcbway.com/) but ran into problems.
In the future, I'll probably use PCBWay for larger orders as JLCPCB looks like they max out at 30 boards for assembly.

If you'd like to see the boards in their current form,
[check them out over at MeowCAD](https://meowcad.com/view_pcb?project=006b550f-e142-4a36-b113-f90155cf7723).
The boards are open source hardware, so
feel free to [download](https://meowcad.com/project?projectId=006b550f-e142-4a36-b113-f90155cf7723) and manufacture, clone, alter, use or sell to your hearts content.


Feedback?  Thoughts?  Be sure to drop us a line in our [feedback section](https://meowcad.com/feedback)


Happy hacking!

###### submitted by \[abetusk\]
