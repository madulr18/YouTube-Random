import pafy
import vlc
import sys
import pickle
from dataclasses import dataclass
from termcolor import colored
from random import *


video_list = []

@dataclass
class Video:
    pafy_video: pafy
    lower_time_fence: int
    upper_time_fence: int

@dataclass
class SavedPlaylist:
    saved_playlist: list


def initialize_playlist(play_url):
    playlist = pafy.get_playlist(play_url)
    for pafy_video in playlist['items']:
        duration = parse_time(pafy_video['pafy'].duration)
        video_list.append(Video(pafy_video, 0, duration))


def parse_time(duration):
    time_parse = duration.split(":")
    hours = int(time_parse[0])
    minutes = int(time_parse[1])
    seconds = int(time_parse[2])
    return hours*3600 + minutes*60 + seconds


def reverse_parse_time(total_time):
    seconds = total_time % 60
    minutes = (total_time // 60) % 60
    hours = (total_time //3600) % 60
    result = "%(#)02d" % {"#" : hours}
    result = result + ":" + "%(#)02d" % {"#": minutes}
    result = result + ":" + "%(#)02d" % {"#": seconds}
    return result


def get_random_video():
    video_index = randint(0, len(video_list)-1)
    video = video_list[video_index]
    return video, video_index


def get_random_start_time(video, random_times):
    if not random_times:
        return 0
    time_range = video.upper_time_fence-video.lower_time_fence
    if time_range < 40:
        return video.lower_time_fence
    else:
        rand_time = randint(video.lower_time_fence, video.upper_time_fence-30)*1000
        return rand_time


def set_time_fences(video, lower, upper):
    video.lower_time_fence = parse_time(lower)
    video.upper_time_fence = parse_time(upper)


def play_next_video(current_index, player, Instance, random_times):
    new_index = (current_index+1) % len(video_list)
    video = video_list[new_index]
    play_video(video.pafy_video, get_random_start_time(video, random_times), player, Instance)
    return new_index


def play_selected_video(index, player, Instance, random_times):
    video = video_list[index]
    play_video(video.pafy_video, get_random_start_time(video, random_times), player, Instance)
    return index


def shuffle_playlist(player, Instance, random_times):
    video, current_index = get_random_video()
    play_video(video.pafy_video, get_random_start_time(video, random_times), player, Instance)
    return current_index


def pause(player):
    player.pause()


def resume(player):
    player.play()


def info(current_index):
    print(current_index, video_list[current_index].pafy_video['pafy'].title)


def save(filename):
    f = open(filename, "wb+")
    current_playlist = SavedPlaylist(video_list)
    print(type(current_playlist))
    pickle.dump(current_playlist, f)
    f.close()


def load(filename):
    f = open(filename, "rb")
    new_playlist = pickle.load(f)
    global video_list
    if len(video_list) == len(new_playlist.saved_playlist):
        for i in range(0, len(video_list)):
            if video_list[i].pafy_video['pafy'].videoid == new_playlist.saved_playlist[i].pafy_video['pafy'].videoid:
                video_list[i].lower_time_fence = new_playlist.saved_playlist[i].lower_time_fence
                video_list[i].upper_time_fence = new_playlist.saved_playlist[i].upper_time_fence
            else:
                print(colored("Unable to load playlist settings\n", "red"))
                break
    else:
        print(colored("Unable to load playlist settings\n", "red"))
    print_song_list()
    f.close()



def print_manual():
    print_commands()
    print("-----------------------------------------------------------------------------\n")
    print_song_list()


def print_commands():
    print("[exit] - stops the media player")
    print("[next] - goes to the next song in the playlist")
    print("[shuffle] - shuffles the next song")
    print("[settime][index][upper][lower] - sets the boundaries for which the song will be played in <HH:MM:SS>")
    print("[setrandom][True/False] - set whether or not random times are played in each song")
    print("[list] - prints the playlist")
    print("[pause] - pauses the media")
    print("[resume] - resumes the media")
    print("[info] - list the info about the current song")
    print("[save][filename] - saves a playlist configuration in a file <filename.obj>")
    print("[load][filename] - load a playlist configuration from a file <filename.obj>")
    print("[play][index] - play a selected song\n")


def print_song_list():
    print("[index], [lower time fence], [upper time fence], [title]")
    for i in range(0, len(video_list)):
        print(i, reverse_parse_time(video_list[i].lower_time_fence), reverse_parse_time(video_list[i].upper_time_fence),
              video_list[i].pafy_video['pafy'].title)
    print("")


def play_video(video, start_time, player, Instance):
    best = video['pafy'].getbest()
    playurl = best.url

    print(playurl)

    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)

    player.play()

    vlc.libvlc_media_player_set_time(player, start_time)


def main():
    if len(sys.argv) != 3:
        print("usage: [playlist url] [Random times]")
        exit(1)
    url = sys.argv[1]
    random_times = (sys.argv[2] != "False")

    initialize_playlist(url)

    video, current_index = get_random_video()
    start_time = get_random_start_time(video, random_times)

    Instance = vlc.Instance()
    player = Instance.media_player_new()

    play_video(video.pafy_video, start_time, player, Instance)

    print_manual()

    command = [""]
    while command[0] != "exit":
        command_string = input("Enter a command; do 'help' for help\n")
        command = command_string.split(" ")
        if command[0] == "settime":
            set_time_fences(video_list[int(command[1])], command[2], command[3])
        elif command[0] == "next":
            current_index = play_next_video(current_index, player, Instance, random_times)
        elif command[0] == "shuffle":
            current_index = shuffle_playlist(player, Instance, random_times)
        elif command[0] == "list":
            print_song_list()
        elif command[0] == "help":
            print_commands()
        elif command[0] == "info":
            info(current_index)
        elif command[0] == "pause":
            pause(player)
        elif command[0] == "resume":
            resume(player)
        elif command[0] == "play":
            index = int(command[1])
            current_index = play_selected_video(index, player, Instance, random_times)
        elif command[0] == "save":
            save(command[1])
        elif command[0] == "load":
            load(command[1])
        elif command[0] == "setrandom":
            random_times = command[1] == "True"
            if random_times:
                print("Random times are now [ON]")
            else:
                print("Random times are now [OFF]")
        elif command[0] == "exit":
            player.stop()
            exit(1)
        print("")


if __name__ == '__main__':
    main()


