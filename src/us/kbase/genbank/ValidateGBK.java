package us.kbase.genbank;

import us.kbase.common.service.Tuple11;
import us.kbase.common.service.UObject;
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
import java.util.List;
import java.util.Map;

/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 11/3/14
 * Time: 3:00 PM
 */
public class ValidateGBK {


        /**
         * @param args
         * @throws Exception
         */
        public ValidateGBK(String[] args) throws Exception {

            File indir = new File(args[0]);

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
        public static void parseAllInDir(int[] pos, File dir, ObjectStorage wc) throws Exception {
            List<File> files = new ArrayList<File>();
            for (File f : dir.listFiles()) {
                if (f.isDirectory()) {
                    parseAllInDir(pos, f, wc);
                } else if (f.getName().endsWith(".gbk")) {
                    files.add(f);
                    System.err.println("Added " + f);
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
        public static void parseGenome(int[] pos, File dir, List<File> gbkFiles, ObjectStorage wc) { //throws Exception
            System.out.println("[" + (pos[0]++) + "] " + dir.getName());
            long time = System.currentTimeMillis();
            try {
                ArrayList ar = GbkUploader.uploadGbk(gbkFiles, "replacewithrealWS", dir.getName(), true);

                Genome gnm = (Genome) ar.get(3);

                ContigSet cs = (ContigSet) ar.get(5);
            } catch (Exception e) {
                System.err.print(e.getMessage());
                System.err.print(e.getStackTrace());
                e.printStackTrace();
            }

        }

        /**
         * @param args
         */
        public final static void main(String[] args) {
            if (args.length == 1) {
                try {
                    ValidateGBK vg = new ValidateGBK(args);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            } else {
                System.out.println("usage: java us.kbase.genbank.ValidateGBK <dir or dir of dirs with GenBank .gbk files>");// <convert y/n> <save y/n>");
            }
        }

}
