# Tuning OBS by Just Asking

### A natural-language control panel for OBS Studio, powered by Claude or ChatGPT

![OBS Natural-Language Tuner](../assets/header.png)

OBS Studio is a remarkable piece of software. It's free, it's open source, and it
runs a huge share of the streams and recordings on the internet. It can do almost
anything.

That "almost anything" is also the problem.

## The settings maze

If you've ever tried to make your microphone sound good in OBS, you know the
feeling. You open the audio mixer, click the gear, find "Filters," and land in a
world of *Noise Suppression*, *Noise Gate*, *Compressor*, and a *3-Band
Equalizer*. Each one has its own dials — an open threshold in decibels, a close
threshold in *more* decibels, attack and release times in milliseconds, a ratio.

Which order should the filters go in? What's a sensible gate threshold? Is −35 dB
too aggressive? The controls are all there, laid out honestly — but they assume you
already speak the language of audio engineering. Most people just want their mic to
stop picking up the fan in the background.

Video and streaming settings are the same story. Base resolution vs. output
resolution. Frame-rate fields. An encoder buried in an output tab, with a bitrate
you're supposed to match to your upload speed. None of it is *hard*, exactly — it's
just a lot of small, unfamiliar decisions stacked on top of each other, and getting
one wrong quietly makes your stream look or sound worse.

It's a lot of friction for something you'd happily describe in a single sentence.

## So describe it in a single sentence

That's the whole idea behind this project. Instead of hunting through menus, you
type what you want:

> *"Clean up my mic and remove background noise."*
> *"Set my output to 1080p at 60 fps."*
> *"Make a 'Starting Soon' scene and switch to it."*
> *"Lower the desktop audio by 6 dB."*

…and it happens. A model reads your request, figures out the right OBS actions, and
applies them — then tells you, in plain language, exactly what it changed.

You bring your own AI key and pick your side: **Claude** (Anthropic) or **ChatGPT**
(OpenAI). Both work identically.

## How it actually works

![How it works](../assets/architecture.png)

The interesting part is *how* the model controls OBS — because there's a naïve way
that doesn't work well, and a robust way that does.

The naïve way is to ask the model to write out an OBS configuration and then apply
it. Models are not great at producing long, exact config blobs, and a single wrong
field can break things silently.

The robust way — the one used here — is **tool calling**. The model isn't asked to
write config. It's handed a catalogue of small, well-defined *tools*:
`apply_audio_filter`, `set_video_settings`, `create_scene`, `set_input_volume`, and
so on. Each tool has a clear description and a strict list of parameters. The model's
only job is to pick the right tools and fill in the arguments — the same way a person
picks the right menu item. The app runs each tool for real and feeds the result back,
so the model can react, correct itself, and keep going until the job is done.

A few design choices make this pleasant to use:

- **One tool set, two brains.** There's a single catalogue of OBS actions. It's
  translated into whatever format Claude or ChatGPT expects, so both providers drive
  the exact same, tested code. Switching providers changes nothing about what the app
  can do.

- **A real, protocol-accurate layer.** Under the tools sits a thin wrapper around
  **obs-websocket** — the control interface built into modern OBS. Every action maps
  one-to-one to an OBS command, so there's no guesswork between "what the model asked
  for" and "what OBS received."

- **Filters that don't pile up.** Ask to clean up your mic twice and you won't end up
  with two noise gates. Applying a filter updates it if it already exists, so you can
  iterate freely.

- **Nothing dangerous by accident.** The tools that can start a *public broadcast* or
  change your stream key are switched off by default. You flip one toggle to enable
  them — so the assistant can happily tweak your EQ all day without any risk of going
  live before you meant to.

- **Your keys stay yours.** API keys and your OBS password live only in the running
  session and are never written to disk. The app talks to OBS on your own machine and
  to the AI provider you chose — nothing else.

## Why this is genuinely useful

The point isn't novelty. It's that a good tool should meet people where they are.

A newcomer shouldn't have to learn what a compressor ratio is before they can sound
clear on a call. A streamer mid-setup shouldn't have to remember which tab hides the
bitrate. The knowledge to configure OBS *well* already exists — it's just locked
behind a wall of small decisions. Putting a language model in front of that wall
turns the wall into a conversation.

And because it's all built on OBS's own control interface, nothing is hidden or
magical. Every change the assistant makes is a change you could have made yourself —
it just made them for you, faster, and explained them afterward.

## Try it

It's a small, open project (MIT licensed). You'll need OBS 28 or newer (the WebSocket
server is built in), Python, and an API key for Claude or ChatGPT.

```bash
git clone https://github.com/madhukeshm/obs-nl-tuner.git
cd obs-nl-tuner
uv sync
uv run streamlit run app.py
```

Enable the WebSocket server in OBS (*Tools → WebSocket Server Settings*), connect,
paste your key, and start typing.

The settings maze doesn't go anywhere — it's still there if you want it. But most of
the time, you can now just say what you want, and get back to streaming.

---

*Built with Streamlit, obs-websocket v5, and the Anthropic and OpenAI SDKs.*
