package us.kbase.genbank.test;

import us.kbase.common.service.Tuple11;
import us.kbase.common.service.UObject;
import us.kbase.genbank.GbkUploader;
import us.kbase.genbank.ObjectStorage;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.ObjectData;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.SaveObjectsParams;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 10/29/14
 * Time: 12:17 AM
 */
public class CommandLineTest {

    String ws = null;

    /**
     * @param args
     * @throws Exception
     */
    public CommandLineTest(String[] args) throws Exception {

        File indir = new File(args[0]);

        if (args.length == 2)
            ws = args[1];

        parseAllInDir(new int[]{1}, indir, new ObjectStorage() {
            @Override
            public List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> saveObjects(
                    String authToken, SaveObjectsParams params) throws Exception {
                //validateObject(validator, params.getObjects().get(0).getName(),
                //			params.getObjects().get(0).getData(), params.getObjects().get(0).getType());
                return null;
            }

            @Override
            public List<ObjectData> getObjects(String authToken,
                                               List<ObjectIdentity> objectIds) throws Exception {
                throw new IllegalStateException("Unsupported method");
            }
        });
    }


    /**
     * @param pos
     * @param dir
     * @param wc
     * @throws Exception
     */
    public void parseAllInDir(int[] pos, File dir, ObjectStorage wc) throws Exception {
        List<File> files = new ArrayList<File>();
        for (File f : dir.listFiles()) {
            if (f.isDirectory()) {
                parseAllInDir(pos, f, wc);
            } else if (f.getName().endsWith(".gbk")) {
                files.add(f);
                System.out.println("Added " + f);
            }
        }
        if (files.size() > 0)
            parseGenome(pos, dir, files, wc);

    }

    /**
     * @param pos
     * @param dir
     * @param gbkFiles
     * @param wc
     * @throws Exception
     */
    public void parseGenome(int[] pos, File dir, List<File> gbkFiles, ObjectStorage wc) throws Exception {
        System.out.println("[" + (pos[0]++) + "] " + dir.getName());
        long time = System.currentTimeMillis();
        ArrayList ar = GbkUploader.uploadGbk(gbkFiles, "replacewithrealWS", dir.getName(), true);

        Genome genome = (Genome) ar.get(4);
        final String outpath = genome.getId() + ".jsonp";
        try {
            PrintWriter out = new PrintWriter(new FileWriter(outpath));
            out.print(UObject.transformObjectToString(genome));
            out.close();
            System.out.println("    wrote: " + outpath);
        } catch (IOException e) {
            System.out.println("Error creating or writing file " + outpath);
            System.out.println("IOException: " + e.getMessage());
        }

        ContigSet contigSet = (ContigSet) ar.get(6);
        final String contigId = genome.getId() + "_ContigSet";
        final String outpath2 = contigId + ".jsonp";
        try {
            PrintWriter out = new PrintWriter(new FileWriter(outpath2));
            out.print(UObject.transformObjectToString(contigSet));
            out.close();
            System.out.println("    wrote: " + outpath2);
        } catch (IOException e) {
            System.out.println("Error creating or writing file " + outpath2);
            System.out.println("IOException: " + e.getMessage());
        }


        if (ws != null) {
            String genomeid = (String)ar.get(2);

            String token = (String)ar.get(3);

            String contigSetId = (String)ar.get(5);

            Map<String, String> meta = ( Map<String, String>)ar.get(7);

            GbkUploader.uploadtoWS(wc, ws, genomeid, token, genome, contigSetId, contigSet, meta);
        }

        System.out.println("    time: " + (System.currentTimeMillis() - time) + " ms");
    }

    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length == 1 || args.length == 2) {
            try {
                CommandLineTest clt = new CommandLineTest(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.test.CommandLineTest <dir or dir of dirs with GenBank .gbk files> <ws name>");// <convert y/n> <save y/n>");
        }
    }

}
