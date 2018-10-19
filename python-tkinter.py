from tkinter import Tk, Entry, Label, Button, Scrollbar, Listbox
from subprocess import call, check_output
from string import ascii_uppercase


def availdiskletter():
    letters = list(ascii_uppercase)

    disk = str(check_output('wmic logicaldisk get caption').split())
    disk = disk.replace('b', '').split(',')
    disk = str(disk[1:])

    diskletters = []

    for x in disk:
        if x.isalpha():
            diskletters.append(x)

    index = 0
    while index < len(diskletters):
        index += 1
        for item in letters:
            if item in diskletters:
                letters.remove(item)

    letters.remove('A')
    letters.remove('B')
    return letters


def app():
    global gui
    gui = Tk()
    gui.title('Simple program')
    gui.geometry('360x130')

    username = Entry()
    usernamelable = Label(text='Username')
    password = Entry(show='*')
    passwordlable = Label(text='Password')
    diskscrollbar = Scrollbar(orient='vertical')
    diskbox = Listbox(width=2, height=4, yscrollcommand=diskscrollbar.set)
    diskscrollbar.config(command=diskbox.yview)
    diskboxlabel = Label(text='Disk letter')
    submitbutton = Button(width=20, text='Press me', command=lambda: conn(username, password, diskbox,
                                                                          result))

    result = Label()

    index = 0
    for item in availdiskletter():
        diskbox.insert(index, item)
        index += 1

    username.grid(row=0, column=1, sticky='NW')
    usernamelable.grid(row=0, column=0, sticky='NW')
    password.grid(row=1, column=1, sticky='NW')
    passwordlable.grid(row=1, column=0, sticky='NW')
    diskscrollbar.grid(row=0, rowspan=3, column=4, sticky='NSEW')
    diskbox.grid(row=0, rowspan=4, column=3, sticky='NW')
    diskboxlabel.grid(row=0, column=2, sticky='NW')
    submitbutton.grid(row=2, column=0, columnspan=3)

    gui.mainloop()


def conn(u, p, d, r):
    username = str(u.get())
    password = str(p.get())
    diskletters = d.curselection()
    diskletter = str(availdiskletter()[diskletters[0]])

    if username != "" and password != "" and len(diskletter) != 0:
        result = call('net use %s: https://webdav.webdav.ru/webdav /user:%s %s /persistent:no' % (
                      diskletter, username, password), shell=True)

        if result == 0:
            r.config(fg='green', text='Success Login. Program close after five seconds')
            r.grid(row=4, column=0, columnspan=3)
            call('explorer %s:' % diskletter, shell=True)
            gui.after(5000, lambda: gui.destroy())
        elif result == 2:
            r.config(fg='red', text='Error! Authentication failed')
            r.grid(row=4, column=0, columnspan=3)
            p.delete(0, 'end')
        else:
            r.config(fg='red', text='Error! Please contact with your system administrator')
            r.grid(row=4, column=0, columnspan=3)
            u.delete(0, 'end')
            p.delete(0, 'end')
    else:
        r.config(fg='red', text='Incorrect username or password. Please try again')
        r.grid(row=4, column=0, columnspan=4)


app()

