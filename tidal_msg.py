
def new_msg(mode="", WID="", TID="", profile={}):

    msg = {
        #header info
        'mode' : mode, #idle,ready,leaf,branch,sap,select
        'WID' : WID,
        'TID' : TID,
        
        'preference' : "", #leaf/branch/sap
        'time_start' : None,
        'profile' : profile,

        #branch info
        'branch_task' : "", #instructions
        'branch_data' : [], #worker results for each new branch
        'branch_data_type' : [], #is each result a leaf or a branch

        #super
        'super_mode':"",      #pending,approved
        'super_task': [],      #instructions of branches of children
        'super_task_ids': [],      #TIDs of child branch task nodes
        'super_approve': [],    #True/false approve or reject child branches
        'super_data':[],         #reasons for rejection or approval (optional)

        #leaf info
        'leaf_task' : "", #instructions 
        'leaf_data' : "", #worker results

        #sap info
        'sap_task' : [], #instructions (solutions from each TID)
        'sap_task_ids' : [], #matching TIDs for the instructions
        'sap_work' : [], #worker results
        'sap_data' : "", #sapper results 
        'sap_rating' : [], #rates 
        'sap_reject' : [] #returns unsatisfactory taskids
    }

    return msg

    
