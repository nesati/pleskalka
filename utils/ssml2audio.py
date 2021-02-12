#! ./venv/bin/python3
"""
Covers speech synthesis markup language to audio.
"""

import logging
import socket
import os

from google.cloud import texttospeech

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

socket.setdefaulttimeout(300)  # hack to avoid timeout error


# noinspection PyTypeChecker
def ssml2audio(ssml_text, outfile):
    """
    Uses google cloud text to speech to convert ssml to audio.

    :param ssml_text: str: speech synthesis markup language file
    :param outfile: str: path to output mp3
    """

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Builds the voice request, selects the language code ("cs-CZ")
    voice = texttospeech.VoiceSelectionParams(
        language_code='cs-CZ',
        name="cs-CZ-Wavenet-A"
    )

    # Selects the type of audio file to return
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.20
    )

    lines = list(filter(lambda line: line.strip() != '', ssml_text.splitlines()))
    paths = []

    if any(map(lambda line: len(line) > 5000, lines)):
        logging.fatal("5000 characters limit exceeded")
        logging.debug(list(filter(lambda line: len(line[1]) > 5000, lines)))
        exit(1)

    filename = os.path.split(outfile)[1]

    for num, ssml_line in enumerate(lines):
        path = f"/tmp/{filename}{num}.mp3"

        # Sets the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_line)

        # Performs the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config,
                                            timeout=300.0)

        # Writes the synthetic audio to the output file.
        with open(path, 'wb') as out:
            out.write(response.audio_content)
            logging.info(f'Audio content written to file {path}')

        paths.append(path)

    # concatenate
    with open("/tmp/paths.txt", "w") as f:
        f.write("\n".join(map(lambda x: f"file '{x}'", paths)))
    os.system(f"ffmpeg -y -f concat -safe 0 -i /tmp/paths.txt '{outfile}.mp3'")

    # delete temporary files
    for file in paths:
        os.remove(file)


if __name__ == '__main__':
    import sys

    ssml2audio(sys.stdin.read(), "output")
