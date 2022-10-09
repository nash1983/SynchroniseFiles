import cgi
import os
from urllib import request
import urllib
import subprocess
import time
import fnmatch
import shutil
import filecmp
import signal
import smtplib


def install_epicor_silently():
    timeout_s = 180
    cmd = ["powershell.exe", f"cd {directory}; .\\{filename} /s /install --Confirm:$false"]
    p = subprocess.Popen(cmd, start_new_session=True)
    try:
        p.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)


def uninstall_epicor_silently():
    try:
        Installed_path1 = f"C:\\Epicor\\SLSDT\\160429-PILOT\\Client\\"
        for exe_filename in os.listdir(Installed_path1):
            if fnmatch.fnmatch(exe_filename, 'ClientInstaller-*.exe'):
                filename1 = exe_filename
                p = subprocess.Popen(["powershell.exe",
                                      f"cd {Installed_path1}; .\\{filename1} --uninstall --force-uninstall --confirm:$False"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                p.communicate()
    except:
        pass


def remove_source_Directory():
    try:
        shutil.rmtree('c:\\Epicor')
        shutil.rmtree('C:\\Users\\ADM-nsurapureddy\\Desktop\\Epicor SLS Public Cloud')
    except:
        pass


def move_installer_2archive():
    try:
        dest_folder = f"C:\\batch\\Epicor_Archive\\"
        source_folder = f"C:\\batch\\Epicor\\"
        for f in os.listdir(source_folder):
            if os.path.isfile(source_folder + f):
                shutil.move(source_folder + f, dest_folder + f)
    except:
        pass


def move_config_2source():
    try:
        dest_folder = f"C:\\Epicor\\SLSDT\\160429-PILOT\\Client\\config\\"
        source_folder = f"C:\\EpicorConfigs\\config\\"
        for f in os.listdir(source_folder):
            if os.path.isfile(source_folder + f):
                shutil.copy2(source_folder + f, dest_folder + f)
    except:
        pass


def restart_remote_computer():
    computer_list = ["PRD-CTX-EC01"]
    for c in computer_list:
        try:
            subprocess.getoutput("shutdown -m \\\\" + c + " -f -r -t 0")
        except:
            pass


def main():
    # restart_remote_computer()
    install_epicor_silently()


class Dispatch:
    # This class represents a synchronization object
    def __init__(self, name=''):
        self.name = name
        self.node_list = []
        self.file_copied_count = 0
        self.folder_copied_count = 0

    def add_node(self, node):
        self.node_list.append(node)

    def compare_nodes(self):
        # This method takes the nodes in the node_list and compares them
        # nodeListLength = len(self.node_list)
        # For each node in the list
        for node in self.node_list:
            # If the list has another item after it, compare them
            if self.node_list.index(node) < len(self.node_list) - 1:
                node3 = self.node_list[self.node_list.index(node) + 1]
                # Passes the two root directories of the nodes to the recursive _compare_directories.
                self._compare_directories(node.root_path, node3.root_path)

    def _compare_directories(self, left, right):
        comparison = filecmp.dircmp(left, right)
        if comparison.common_dirs:
            for d in comparison.common_dirs:
                self._compare_directories(os.path.join(left, d), os.path.join(right, d))
        if comparison.left_only:
            self._copy(comparison.left_only, left, right)
        # if comparison.right_only:
        # self._copy(comparison.right_only, right, left)
        left_newer = []
        # right_newer = []

        if comparison.diff_files:
            for d in comparison.diff_files:
                l_modified = os.stat(os.path.join(left, d)).st_mtime
                r_modified = os.stat(os.path.join(right, d)).st_mtime
                if l_modified > r_modified:
                    left_newer.append(d)
                # else:
                # right_newer.append(d)
        self._copy(left_newer, left, right)
        # self._copy(right_newer, right, left)

    def _copy(self, file_list, src, dest):
        # This method copies a list of files from a source node to a destination node
        for f in file_list:
            srcpath = os.path.join(src, os.path.basename(f))
            if os.path.isdir(srcpath):
                shutil.copytree(srcpath, os.path.join(dest, os.path.basename(f)))
                self.folder_copied_count = self.folder_copied_count + 1
                with smtplib.SMTP('relay.rslc.local', 25) as smtp:
                    body2 = (
                            f"*********************************************** \n"
                            f"Source path:{srcpath}  \n "
                            f"Destination path:{dest} \n "
                            f"*********************************************** \n"
                            f'Copied sub-directory \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(
                        srcpath) + '\" to \"' + dest + '\"')
                    smtp.sendmail(from_addr='easupport@boltonclarke.com.au',
                                  to_addrs='nsurapureddy@boltonclarke.com.au,lcooper1@boltonclarke.com.au',
                                  msg=f"Subject:Epicor Installation was Successful below sub-directory was transferred from Source to Destination \n\n {body2}")
            else:
                shutil.copy2(srcpath, dest)
                self.file_copied_count = self.file_copied_count + 1
                with smtplib.SMTP('relay.rslc.local', 25) as smtp:
                    body2 = (
                            f"*********************************************** \n"
                            f"Source path:{srcpath}  \n "
                            f"Destination path:{dest} \n "
                            f"*********************************************** \n"
                            f'Copied file \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(
                        srcpath) + '\" to \"' + dest + '\"')
                    smtp.sendmail(from_addr='easupport@boltonclarke.com.au',
                                  to_addrs='nsurapureddy@boltonclarke.com.au;lcooper1@boltonclarke.com.au',
                                  msg=f"Subject:Epicor Installation was Successful below file was transferred from Source to Destination \n\n {body2}")


class Node:
    # This class represents a node in a dispatch synchronization

    def __init__(self, path, name=''):
        self.name = name
        self.root_path = os.path.abspath(path)
        self.file_list = os.listdir(self.root_path)


url = "https://download.epicorsaas.com/d?siteId=160429&environment=PILOT&customInstallLocation="
r = urllib.request.urlopen(url)
_, params = cgi.parse_header(r.headers.get("Content-Disposition", ''))
filename = params['filename']
directory = f"c:\\batch\\Epicor\\"
file_location = f"c:\\batch\\Epicor\\{filename}"
response = request.urlretrieve(url, file_location)
if __name__ == "__main__":
    main()
    time.sleep(10)
    move_config_2source()
    time.sleep(600)
    my_dispatch = Dispatch('Client')
    node1 = Node(f"C:\\Epicor\\SLSDT\\160429-PILOT\\Client\\", 'node1')
    node2 = Node('\\\\' + 'PRD-CTX-EC01' + '\\C$' + '\\Program Files (x86)\\epicor\\Client\\', 'node2')
    my_dispatch.add_node(node1)
    my_dispatch.add_node(node2)
    my_dispatch.compare_nodes()
    move_installer_2archive()
    