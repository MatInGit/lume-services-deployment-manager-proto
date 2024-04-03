import k2eg
import os
import uuid

def initialise_k2eg():
    """Initialise a K2EG client
    Returns:
        k2eg: K2EG client
    """
    k = k2eg.dml('env', "app-test-4")
    return k

def monitor(pv_list:list, handler:callable, client:k2eg):
    """Monitor a list of PVs with a handler function
    Args:
        pv_list (list): List of PVs to monitor
        handler (callable): Function to handle the PV data
        client (k2eg, optional): K2EG client.
    """
    client.monitor_many(pv_list, handler)