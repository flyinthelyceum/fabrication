# Working on this repo as a student

You do not need to know git to help build the CNC station. Read this once; it is
short on purpose.

## What this repo is

Everything about the station that can be written down lives here: the CAD that
draws every part, the cut files, the tool list, and the job cards for the physical
build. When the station is finished, this repo is the record of how it was made and
who made it. Your name goes in that record.

## The one idea: a job is an issue

Every piece of work is an **Issue** on this repo (the "Issues" tab at the top of the
page). One issue is one job: what to make, which files to use, what has to be true
before you start, and what "done" looks like. Issues are labelled by **lane**
(`lane:spine`, `lane:power`, ...) and by **who may do it**:

- `who:student` you can do it on your own once someone has shown you the tool
- `who:foreman+jared` cutting on the Shapeoko or the track saw, with Mr. Reasy in the room
- `who:jared` mains electricity, the safety interlock, the waterjet. Not yours, do not touch

Lanes are independent. Pick a lane, and nothing in it waits on another lane until
the job card says JOIN.

## How to work

1. **Get a GitHub account** with your school email. Ask Mr. Reasy to add you to the
   repo if you cannot see it.
2. **Claim a job.** Open the issue and post a comment that says `claiming`. One job
   per person at a time. If someone else has already claimed it, pick another.
3. **Read the whole card before touching anything.** The BEFORE line lists what must
   already be true. If it is not true, comment on the issue saying what is missing
   and pick another job. Do not work around a missing prerequisite.
4. **Do the work.**
5. **Report with a photo and a number.** The DONE WHEN line tells you exactly what
   to photograph and what to measure. Post both as a comment on the issue. A
   report without the number is not a report. Photos go straight in from the
   GitHub app on your phone.
6. Mr. Reasy closes the issue when the done check is met, or comments with what
   still needs doing. An issue you opened stays yours until it is closed.

## Rules that keep the shop safe and the repo honest

- **Never plug in the power mock-up.** The 24 V side is yours to build; anything
  that touches a wall outlet is `who:jared`.
- **Measure, do not estimate.** If a card asks for a number, use calipers or the
  20 mm bench grid and write down what you read. If the reading disagrees with
  the drawing, that is the most useful comment you can make; say so plainly.
- **Nothing leaves the shop without a picture.** If you made a thing, photograph
  it on the grid before it goes anywhere.
- **Do not push to `master`.** Nobody does, including Mr. Reasy. If you ever change
  a file in this repo (a CSV, a drawing, code), it goes on a branch and comes in as
  a pull request that he merges. Your first few contributions will be comments on
  issues, which needs none of that.
- **Ask on the issue.** A question posted there is answered once for everyone and
  stays findable by the next person who hits the same thing.

## When you are ready to change files

Only once you have a few closed issues behind you.

1. On GitHub, press **Fork** to make your own copy of the repo.
2. In your copy, make a branch named after the issue, for example `issue-14-spine-slots`.
3. Change the file. Keep the change to what the issue asks for and nothing else.
4. Open a **pull request** from your branch to this repo's `master`. In the
   description, write `Closes #14` (the issue number) and what you measured or
   checked.
5. Mr. Reasy reviews it. He may ask for changes. That is normal and is not a
   verdict on you.

Measured dimensions never go in this repo directly; they live in the
[components](https://github.com/flyinthelyceum/components) library, one writer, so
that a number exists in exactly one place. If your job produces a measurement of a
part, post it on the issue and it will be recorded there.

## Where the plan lives

The build sequence with every job card is in the issues under the milestone
**CNC Station: physical build**. The design brief that explains why the station is
the shape it is belongs to Mr. Reasy; ask him for it if you want the reasons, not
just the steps.
