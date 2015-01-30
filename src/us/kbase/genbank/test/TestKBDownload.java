package us.kbase.genbank.test;

import us.kbase.auth.AuthService;
import us.kbase.auth.AuthToken;
import us.kbase.auth.AuthUser;
import us.kbase.common.service.Tuple11;
import us.kbase.genbank.GenometoGbk;
import us.kbase.workspace.ListObjectsParams;
import us.kbase.workspace.WorkspaceClient;

import java.io.File;
import java.net.URL;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 1/29/15
 * Time: 7:50 PM
 */
public class TestKBDownload {

    boolean isTest;

    String[] argsPossible = {"-w", "--workspace_name", "-wu", "--workspace_service_url", "-su", "--shock_url", "-wd", "--working_directory", "--test"};
    String[] argsPossibleMap = {"wsn", "wsn", "wsu", "wsu", "shocku", "shocku", "wd", "wd", "t"};

    String wsname, shockurl, wsurl;
    File workdir;

    /**
     * @param args
     */
    public TestKBDownload(String[] args) {

        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes")
                            || args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        if (workdir == null) {
            workdir = new File(Paths.get(".").toAbsolutePath().normalize().toString());
        } else if (!workdir.exists()) {
            workdir.mkdirs();
        }


        try {
            WorkspaceClient wc = null;

            String user = System.getProperty("test.user");
            String pwd = System.getProperty("test.pwd");

            String kbtok = System.getenv("KB_AUTH_TOKEN");

            if (isTest) {
                System.out.println("using test mode");
                AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                wc = new WorkspaceClient(new URL(wsurl), at);
            } else {
                wc = new WorkspaceClient(new URL(wsurl), new AuthToken(kbtok));
            }

            wc.setAuthAllowedForHttp(true);

            ListObjectsParams lop = new ListObjectsParams();

            List<String> lw = new ArrayList();
            lw.add("KBasePublicGenomesV5");
            lop.withType("KBaseGenomes.Genome").withWorkspaces(lw);

            List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> getobj =
                    wc.listObjects(lop);

            int count = 0;
            for (Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> t : getobj) {
                System.out.println(count + "\t" + t.getE2() + "\t" + ((double) t.getE10() / (double) (1024 ^ 2)) + "M");
                count++;

                try {

                    List<String> ar = new ArrayList();

                    ar.add("--workspace_name");
                    ar.add("KBasePublicGenomesV5");
                    ar.add("--workspace_service_url");
                    ar.add("https://kbase.us/services/ws");
                    ar.add("--object_name");
                    ar.add(t.getE2());
                    ar.add("--working_directory");
                    ar.add(workdir.getAbsolutePath() + "/" + t.getE2());

                    if (isTest) {
                        ar.add("--test");
                        ar.add("T");
                    }
                    String[] argsgt = new String[ar.size()];
                    int count2 = 0;
                    for (Object obj : ar) {
                        argsgt[count2] = obj.toString();
                        count2++;
                    }

                    GenometoGbk gt = new GenometoGbk(wc);
                    gt.init(argsgt);
                    gt.run();
                } catch (Exception e) {
                    System.out.println("Error for genome " + t.getE2());
                    e.printStackTrace();
                }

            }
        } catch (Exception e) {
            e.printStackTrace();
        }


    }


    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length >= 4 || args.length <= 10) {
            try {
                TestKBDownload clt = new TestKBDownload(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.ConvertGBK " +
                    "<-w or --workspace_name ws name> " +
                    "<-wu or --workspace_service_url ws url> " +
                    "<-su or --shock_url shock url> " +
                    "<-wd or --working_directory> " +
                    "<--test>");
        }
    }
}


/*
    public TestKBDownload(String[] args) {

        for (int i = 0; i < args.length; i++) {
            int index = Arrays.asList(argsPossible).indexOf(args[i]);
            if (index > -1) {
                if (argsPossibleMap[index].equals("wsn")) {
                    wsname = args[i + 1];
                } else if (argsPossibleMap[index].equals("wsu")) {
                    wsurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("shocku")) {
                    shockurl = args[i + 1];
                } else if (argsPossibleMap[index].equals("wd")) {
                    workdir = new File(args[i + 1]);
                } else if (argsPossibleMap[index].equals("t")) {
                    if (args[i + 1].equalsIgnoreCase("Y") || args[i + 1].equalsIgnoreCase("yes")
                            || args[i + 1].equalsIgnoreCase("T") || args[i + 1].equalsIgnoreCase("TRUE"))
                        isTest = true;
                }
            }
        }

        if (workdir == null) {
            workdir = new File(Paths.get(".").toAbsolutePath().normalize().toString());
        } else if (!workdir.exists()) {
            workdir.mkdirs();
        }


        ObjectMapper mapper = UObject.getMapper();


        try {
            WorkspaceClient wc = null;

            String user = System.getProperty("test.user");
            String pwd = System.getProperty("test.pwd");

            String kbtok = System.getenv("KB_AUTH_TOKEN");

            if (isTest) {
                System.out.println("using test mode");
                AuthToken at = ((AuthUser) AuthService.login(user, pwd)).getToken();
                wc = new WorkspaceClient(new URL(wsurl), at);
            } else {
                wc = new WorkspaceClient(new URL(wsurl), new AuthToken(kbtok));
            }

            wc.setAuthAllowedForHttp(true);

            ListObjectsParams lop = new ListObjectsParams();

            List<String> lw = new ArrayList();
            lw.add("KBasePublicGenomesV5");
            lop.withType("KBaseGenomes.Genome").withWorkspaces(lw);

            List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> getobj =
                    wc.listObjects(lop);

            int count = 0;
            for (Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> t : getobj) {
                System.out.println(count + "\t" + t.getE2() + "\t" + ((double) t.getE10() / (double) (1024 ^ 3)));
                count++;

                List<ObjectIdentity> objectIds = new ArrayList<ObjectIdentity>();
                String objectname = t.getE2();
                ObjectIdentity genobj = new ObjectIdentity();
                genobj.setName(objectname);

                genobj.setWorkspace(wsname);
                objectIds.add(genobj);

                System.out.println("getting Genome object " + wsname + "/" + objectname);
                long startg = System.currentTimeMillis();
                List<ObjectData> lod = wc.getObjects(objectIds);
                final UObject data1 = lod.get(0).getData();
                long endg = System.currentTimeMillis();

                final double doub = (double) (endg - startg) / (double) 1000;
                NumberFormat df = DecimalFormat.getInstance();
                df.setMinimumFractionDigits(2);
                df.setMaximumFractionDigits(2);
                df.setRoundingMode(RoundingMode.DOWN);
                String result = df.format(doub);
                System.out.println("got Genome in " + result + " s");

                Genome genome = data1.asClassInstance(Genome.class);
                String contigref = genome.getContigsetRef();

                String outpath = workdir + "/" + objectname + ".jsonp";

                try {
                    PrintWriter out = new PrintWriter(new FileWriter(outpath));
                    out.print(UObject.transformObjectToString(genome));
                    out.close();
                    System.out.println("    wrote: " + outpath);
                } catch (IOException e) {
                    System.err.println("Error creating or writing file " + outpath);
                    System.err.println("IOException: " + e.getMessage());
                }

                GetObjectInfoNewParams params = new GetObjectInfoNewParams();
                params.setObjects(objectIds);
                params.setIncludeMetadata(1L);

                List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> oinfo = wc.getObjectInfoNew(params);
                Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> tup = oinfo.get(0);

                final double doub2 = (double) tup.getE10() / (double) (1024 * 1024);
                df = DecimalFormat.getInstance();
                df.setMinimumFractionDigits(2);
                df.setMaximumFractionDigits(2);
                df.setRoundingMode(RoundingMode.DOWN);
                String result2 = df.format(doub2);

                //DecimalFormat df = new DecimalFormat("0.00##");
                //String result = df.format(doub);

                System.out.println("got Genome object size " + result2 + "M");

                List<ObjectIdentity> objectIds2 = new ArrayList<ObjectIdentity>();
                ObjectIdentity contigobj = new ObjectIdentity();
                contigobj.setRef(contigref);
                objectIds2.add(contigobj);
                System.out.println("got contigref " + contigref);
                try {

                    long startg2 = System.currentTimeMillis();
                    List<ObjectData> lod2 = wc.getObjects(objectIds2);
                    long endg2 = System.currentTimeMillis();
                    final UObject data2 = lod2.get(0).getData();
                    final double doub3 = (double) (endg2 - startg2) / (double) 1000;
                    df = DecimalFormat.getInstance();
                    df.setMinimumFractionDigits(2);
                    df.setMaximumFractionDigits(2);
                    df.setRoundingMode(RoundingMode.DOWN);
                    String result3 = df.format(doub3);

                    System.out.println("got ContigSet in " + result3 + " s");

                    ContigSet contigSet = data2.asClassInstance(ContigSet.class);

                    String cname = null;
                    if (contigSet.getName() != null) {
                        cname = contigSet.getName();
                    } else if (genome.getId() != null) {
                        cname = genome.getId() + "_ContigSet";
                    }
                    String outpath2 = workdir + "/" + cname + ".jsonp";

                    try {
                        PrintWriter out = new PrintWriter(new FileWriter(outpath2));
                        out.print(UObject.transformObjectToString(contigSet));
                        out.close();
                        System.out.println("    wrote: " + outpath2);
                    } catch (IOException e) {
                        System.err.println("Error creating or writing file " + outpath2);
                        System.err.println("IOException: " + e.getMessage());
                    }

                    GetObjectInfoNewParams params2 = new GetObjectInfoNewParams();
                    params2.setObjects(objectIds2);
                    params2.setIncludeMetadata(1L);
                    //System.out.println(Instrumentation.getObjectSize(contigSet));
                    List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> oinfo2 = wc.getObjectInfoNew(params2);
                    Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>> tup2 = oinfo2.get(0);

                    final double doub4 = (double) tup2.getE10() / (double) (1024 * 1024);
                    df = DecimalFormat.getInstance();
                    df.setMinimumFractionDigits(2);
                    df.setMaximumFractionDigits(2);
                    df.setRoundingMode(RoundingMode.DOWN);
                    String result4 = df.format(doub4);

                    System.out.println("got ContigSet object number " + contigSet.getContigs().size() + ", size " + result4 + "M");



                    String[] argscg = {};
                    ConvertGBK cg = new ConvertGBK(argscg);


                } catch (Exception e) {
                    System.err.println("ContigSet not found in workspace.");
                }
            }
        } catch (AuthException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (JsonClientException e) {
            e.printStackTrace();
        }


    }*/
