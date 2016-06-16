package us.kbase.kbaseenigmametals;

import us.kbase.common.service.JsonServerServlet;

//BEGIN_HEADER
//END_HEADER

/**
 * <p>Original spec-file module name: KBaseEnigmaMetals</p>
 * <pre>
 * </pre>
 */
public class KBaseEnigmaMetalsServer extends JsonServerServlet {
    private static final long serialVersionUID = 1L;

    //BEGIN_CLASS_HEADER
    //END_CLASS_HEADER

    public KBaseEnigmaMetalsServer() throws Exception {
        super("KBaseEnigmaMetals");
        //BEGIN_CONSTRUCTOR
        //END_CONSTRUCTOR
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.out.println("Usage: <program> <server_port>");
            return;
        }
        new KBaseEnigmaMetalsServer().startupServer(Integer.parseInt(args[0]));
    }
}
