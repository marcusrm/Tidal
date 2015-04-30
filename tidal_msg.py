
def new_msg(mode="", WID="", TID="", profile={}):

    msg = {
        #header info
        'mode'                  : mode,     #idle,ready,leaf,branch,super,sap,select,complete
        'WID'                   : WID,
        'TID'                   : TID,
        
        'preference'            : "",       #leaf/branch/sap
        'time_start'            : None,
        'time_end'              : None,
        'profile'               : profile,
        'ready_flag'            : "decline",

        #branch info
        'branch_task'           : "",       #instructions
        'branch_data'           : [],       #worker results for each new branch
        'branch_data_type'      : [],       #is each result a leaf or a branch

        #super
        'super_mode'            :'idle',   # Supervision process for this task is unapproved' or 'approved'
        'super_child_num'       :0,
        'super_child_data'      :[],
        'super_child_data_type' :"",
        'super_child_data_pred' :[],
        'super_task_id'         :"",       # TIDs of child branch task nodes
        'super_approve'         :False,       # True/false approve or reject child branches
        'super_feedback'        :"",       # Reasons for rejection or approval (optional)

        #leaf info
        'leaf_task'             : "",       #instructions 
        'leaf_data'             : "",       #worker results

        #sap info
        'sap_task'              : [],       #instructions (solutions from each TID)
        'sap_task_ids'          : [],       #matching TIDs for the instructions
        'sap_work'              : [],       #worker results
        'sap_data'              : "",       #sapper results 
        'sap_rating'            : [],       #rates 
        'sap_reject'            : []        #returns unsatisfactory taskids
    }

    return msg

    
