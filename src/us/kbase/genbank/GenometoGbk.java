package us.kbase.genbank;

import com.fasterxml.jackson.databind.ObjectMapper;
import us.kbase.common.service.Tuple4;
import us.kbase.common.service.UObject;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Feature;
import us.kbase.kbasegenomes.Genome;

import java.io.File;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.List;


/**
 * Created by Marcin Joachimiak
 * User: marcin
 * Date: 12/17/14
 * Time: 9:41 PM
 */
public class GenometoGbk {

    //NC_009925.jsonp NC_009925_ContigSet.jsonp

    boolean isTest = true;

    Genome genome;
    ContigSet contigSet;

    final static String molecule_type_short = "DNA";
    final static String molecule_type_long = "genome DNA";

    /**
     * @param args
     * @throws Exception
     */
    public GenometoGbk(String[] args) throws Exception {

        /*TODO get object with references and handles from WS */
        ObjectMapper mapper = UObject.getMapper();//new ObjectMapper();
        File loadGenome = new File(args[0]);
        File loadContigs = new File(args[1]);
        genome = mapper.readValue(loadGenome, Genome.class);
        contigSet = mapper.readValue(loadContigs, ContigSet.class);

        System.out.println(genome.getTaxonomy());

        List<Contig> contigs = contigSet.getContigs();
        for (int j = 0; j < contigs.size(); j++) {

            Contig curcontig = contigs.get(j);
            StringBuffer out = new StringBuffer("");
            //out += "LOCUS       NC_005213             " + curcontig.getLength() + " bp    " + molecule_type_short + "     circular CON 10-JUN-2013\n";
            out.append("LOCUS       " + "" + "             " + curcontig.getLength() + " bp    " +
                    molecule_type_short + "\n");// + "     circular CON 10-JUN-2013\n");
            out.append("DEFINITION  " + genome.getScientificName() + " genome.\n");
            //out.append("ACCESSION   NC_005213\n");
            //out.append("VERSION     NC_005213.1  GI:38349555\n");
            //out += "DBLINK      Project: 58009\n";
            //out += "            BioProject: PRJNA58009\n";
            out.append("KEYWORDS    .\n");
            out.append("SOURCE      " + genome.getScientificName() + "\n");
            out.append("  ORGANISM  " + genome.getScientificName() + "\n");
            final String rawTaxonomy = genome.getTaxonomy();

            String[] alltax = rawTaxonomy.split(" ");

            StringBuffer formatTax = new StringBuffer("");

            int counter = 0;
            int index = 0;
            while (index < alltax.length) {
                formatTax.append(alltax[index]);
                if (index < alltax.length - 1)
                    formatTax.append(" ");
                counter += alltax[index].length() + 1;
                index++;
                if (counter >= 65 || rawTaxonomy.length() < 80) {
                    formatTax.append("\n");
                    formatTax.append("            ");
                    counter = 0;
                }
            }

            out.append("            " + formatTax + ".\n");

            /*TODO populate references in Genome objects */
            /*
             //typedef tuple<int id, string source_db, string article_title, string link, string pubdate, string authors, string journal_name> publication;
            List<Tuple7<Long, String, String, String, String, String, String>> pubs = genome.getPublications();

            for (int k = 0; k < pubs.size(); k++) {
                Tuple7<Long, String, String, String, String, String, String> curpub = pubs.get(k);

                System.out.println(genome.getTaxonomy());
                System.out.println(curpub.getE6());

                out += "REFERENCE   1  (bases " + 1 + " to " + curcontig.getLength() + ")\n";
                out += "  AUTHORS   ";//Waters,E., Hohn,M.J., Ahel,I., Graham,D.E., Adams,M.D.,\n";

                for(int m=0;m<(curpub.getE6()).length();m++) {
                out+=
                //out += "            Barnstead,M., Beeson,K.Y., Bibbs,L., Bolanos,R., Keller,M.,\n";//59
                }
                out += "  TITLE     "+curpub.getE3()+"\n";//64
                out += "  JOURNAL   "+curpub.getE7()+"\n";
                //TODO Genome object missing JOURNAL volume issue pages etc.
                //+" 100 (22), 12984-12988 (2003)\n";
                if (curpub.getE2().equalsIgnoreCase("PUBMED"))
                    out += "   PUBMED   " + curpub.getE1() + "\n";
            }
        */

            //out += "COMMENT     PROVISIONAL REFSEQ: This record has not yet been subject to final\n";
            //out += "            NCBI review. The reference sequence was derived from AE017199.\n";
            //out += "            COMPLETENESS: full length.\n";


            out.append("FEATURES             Location/Qualifiers\n");
            out.append("     source          1.." + curcontig.getLength() + "\n");
            out.append("                     /organism=\"" + genome.getScientificName() + "\"\n");
            out.append("                     /mol_type=\"" + molecule_type_long + "\"\n");
            //out += "                     /strain=\"\"\n";
            out.append("                     /db_xref=\"taxon:" + genome.getSourceId() + "\"\n");

            List<Feature> features = genome.getFeatures();


            for (int i = 0; i < features.size(); i++) {
                Feature cur = features.get(i);
                List<Tuple4<java.lang.String, java.lang.Long, java.lang.String, java.lang.Long>> location = cur.getLocation();
                cur.getAliases();
                //out += "gene            complement(join(490883..490885,1..879))\n";
                //"location":[["kb|g.0.c.1",3378378,"+",1368]]

                //System.out.println("*" + cur.getType() + "*");

                String id = null;
                final List<String> aliases = cur.getAliases();
                if (aliases != null)
                    id = aliases.get(0);
                else
                    id = cur.getId();

                String function = cur.getFunction();
                String[] allfunction = function.split(" ");
                boolean debug = false;
                /*
                if (id.equals("P75809")) {
                    debug = true;
                    System.out.println("allfunction " + allfunction.length + "\t" + function.length());
                }*/
                StringBuffer formatNote = getAnnotation(function, allfunction, 51, 58, debug);
                StringBuffer formatFunction = getAnnotation(function, allfunction, 48, 58, debug);//51,58);


                /*TODO add operons and promoteres and terminators as gene features ? */
                if (id.indexOf(".opr.") == -1 && id.indexOf(".prm.") == -1 && id.indexOf(".trm.") == -1) {

                    if (cur.getType().equals("CDS")) //id.indexOf(".rna.") == -1)
                        out.append("     gene            ");
                    else {
                        if (function.indexOf("tRNA") != -1) {
                            out.append("     tRNA            ");
                        } else {
                            out.append("     misc_RNA        ");
                        }
                    }
                    out = getCDS(out, location);
                    out.append("                     /gene=\"" + id + "\"\n");
                    //out += "                     /db_xref=\"GeneID:2732620\"\n";
                    if (cur.getType().equals("CDS")) {
                        out.append("     CDS             ");
                        out = getCDS(out, location);
                        out.append("                     /gene=\"" + id + "\"\n");
                    }

                    out.append("                     /note=\"" + formatNote);
                    //out += "                     /codon_start=1\n";
                    //out += "                     /transl_table=11\n";
                    out.append("                     /product=\"" + id + "\"\n");
                    out.append("                     /function=\"" + formatFunction);

                    if (cur.getType().equals("CDS"))
                        out.append("                     /protein_id=\"" + id + "\"\n");
                    //out += "                     /db_xref=\"GI:41614797\"\n";
                    //out += "                     /db_xref=\"GeneID:2732620\"\n";

                    //gene

                    final String proteinTranslation = cur.getProteinTranslation();
                    //System.out.println(proteinTranslation);
                    if (proteinTranslation != null)
                        out.append("                     /translation=\"" + formatString(proteinTranslation, 44, 58));
                    //else
                    //    System.out.println("op? " + id);
                }
            }


            out.append("ORIGIN\n");
            out.append(formatDNASequence(curcontig.getSequence(), 10, 60));
            //out += "        1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa\n";//10

            int start = Math.max(0, args[0].lastIndexOf("/"));
            int end = args[0].lastIndexOf(".");
            final String outpath = args[0].substring(start, end) + "_fromKBaseGenome.gbk";
            System.out.println("writing " + outpath);
            File outf = new File(outpath);
            PrintWriter pw = new PrintWriter(outf);
            pw.print(out);
            pw.close();
        }
    }

    /**
     * @param function
     * @param allfunction
     * @return
     */
    private StringBuffer getAnnotation(String function, String[] allfunction, int first, int next, boolean debug) {
        if (debug)
            System.out.println("getAnnotation " + first + "\t" + next);
        StringBuffer formatFunction = new StringBuffer("");
        //73
        boolean isfirst = true;
        if (function.length() < first) {
            formatFunction.append(function + "\"\n");
        } else {
            int counter2 = 0;//allfunction[0].length();
            int index2 = 0;//allfunction[0].length();
            while (index2 < allfunction.length) {
                //if (debug) {
                //System.out.println("allfunction index2 " + index2 + "\t" + allfunction[index2]);
                //    System.out.println("allfunction counter2 1 " + counter2);
                //}
                counter2 = +allfunction[index2].length() + 1;
                if (debug) {
                    StringBuffer out = new StringBuffer("");
                    out.append(index2 + "\t");
                    out.append(counter2 + "\t");
                    out.append((index2 + 1 < allfunction.length ? (counter2 + allfunction[index2 + 1].length()) : "NaN") + "\t");
                    out.append(allfunction[index2].length() + "\t");
                    out.append((index2 + 1 < allfunction.length ? allfunction[index2 + 1].length() : "NaN") + "\t");
                    out.append(allfunction[index2] + "\t");
                    out.append((index2 + 1 < allfunction.length ? allfunction[index2 + 1] : "NaN") + "\t");
                    System.out.println("allfunction " + out);
                }


                formatFunction.append(allfunction[index2]);
                if (index2 < allfunction.length - 1)
                    formatFunction.append(" ");

                if (index2 + 1 < allfunction.length) {
                    counter2 += allfunction[index2 + 1].length() + 1;
                    if (debug)
                        System.out.println(counter2);
                    //if (debug)
                    //    System.out.println("allfunction length " + (allfunction[index2].length() + 1) + "\tcounter2 " + counter2);
                    index2++;
                    if (((isfirst && counter2 >= first) || counter2 >= next)) {//&& index2 < allfunction.length
                        if (debug)
                            System.out.println("new line");
                        if (isfirst)
                            isfirst = false;
                        formatFunction.append("\n");
                        if (index2 < allfunction.length - 1)
                            formatFunction.append("                     ");
                        counter2 = 0;
                    } else if (index2 == allfunction.length) {
                        if (debug)
                            System.out.println("new line end");
                        formatFunction.append("\"\n");
                        break;
                    }
                } else {
                    if (debug)
                        System.out.println("new line end");
                    formatFunction.append("\"\n");
                    break;
                }
            }
        }
        if (formatFunction.length() == 0) {
            formatFunction.append("\"\n");
        }
        return formatFunction;
    }

    /**
     * @param out
     * @param location
     * @return
     */
    private StringBuffer getCDS(StringBuffer out, List<Tuple4<String, Long, String, Long>> location) {
        int added = 0;
        boolean complement = false;
        boolean join = false;
        for (int n = 0; n < location.size(); n++) {
            Tuple4<String, Long, String, Long> now4 = location.get(n);
            if (added == 0 && now4.getE3().equals("-")) {
                out.append("complement(");

                complement = true;
            }
            if (location.size() > 1) {
                if (added == 0)
                    out.append("join(");
                join = true;
            }

            out.append(now4.getE2() + ".." + (now4.getE2() + (long) now4.getE4()));

            if (location.size() > 0 && n < location.size() - 1)
                out.append(",");
            added++;
        }
        if (complement && join)
            out.append("))\n");
        else if (complement || join) {
            out.append(")\n");
        } else
            out.append("\n");

        return out;
    }


    /**
     * @param s
     * @param one
     * @param two
     * @return
     */
    public StringBuffer formatString(String s, int one, int two) {
        //StringBuilder out = new StringBuilder("");
        StringBuffer out = new StringBuffer("");
        boolean first = true;
        for (int start = 0; start < s.length(); ) {
            if (first) {
                int last = Math.min(s.length(), start + one);
                boolean isLast = false;
                if (last == s.length())
                    isLast = true;
                out.append(s.substring(start, last));
                if (isLast)
                    out.append("\"\n");
                else {
                    out.append("\n");
                }
                first = false;
                start += one;
            } else {
                int last = Math.min(s.length(), start + two);
                //System.out.println(s.length() + "\t" + (start + two));
                out.append("                     ");
                boolean isLast = false;
                if (last == s.length())
                    isLast = true;
                out.append(s.substring(start, last));
                start += two;
                if (isLast) {
                    //out.append(s.substring(start, s.length()-1));
                    out.append("\"\n");
                }
                //} else if (start < s.length()) {
                else
                    out.append("\n");
                //} //else if (start < s.length()) {
                //    out.append("\n");
                //} //else
                //  out.append("\n");
            }
        }

        return out;
    }

    /**
     * @param s
     * @param charnum
     * @param linenum
     * @return
     */
    public StringBuffer formatDNASequence(String s, int charnum, int linenum) {
        //StringBuilder out = new StringBuilder("");
        StringBuffer out = new StringBuffer("");

        //out += "        1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa\n";//10

        out.append("        1 ");
        int index = 1;
        int counter = 0;
        for (int last = 0; last < s.length(); ) {
            int end = Math.min(s.length(), last + charnum);
            //if (end > s.length())
            //   end = s.length();
            //System.out.println("DNA " + last + "\t" + end);
            out.append(s.substring(last, end));
            last += charnum;
            counter++;
            if (counter == 6 && s.length() > end) {
                out.append("\n");
                index += 60;
                String indexStr = "" + index;
                int len = indexStr.length();
                char[] ch = new char[9 - len];
                Arrays.fill(ch, ' ');
                String padStr = new String(ch);
                out.append(padStr + indexStr + " ");
                counter = 0;
            } else
                out.append(" ");
        }
        if (out.charAt(out.length() - 1) == (' '))
            out.deleteCharAt(out.length() - 1);

        return out;
    }


    /**
     * @param args
     */
    public final static void main(String[] args) {
        if (args.length == 1 || args.length == 2) {
            try {
                GenometoGbk gtg = new GenometoGbk(args);
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("usage: java us.kbase.genbank.GenometoGbk <Genome .json (XXXX.json)> <ContigSet .json (XXXX_ContigSet.json)>");// <convert y/n> <save y/n>");
        }
    }

}


 /*
LOCUS       NC_005213             490885 bp    DNA     circular CON 10-JUN-2013
 DEFINITION  Nanoarchaeum equitans Kin4-M chromosome, complete genome.
 ACCESSION   NC_005213
 VERSION     NC_005213.1  GI:38349555
 DBLINK      Project: 58009
             BioProject: PRJNA58009
 KEYWORDS    .
 SOURCE      Nanoarchaeum equitans Kin4-M
   ORGANISM  Nanoarchaeum equitans Kin4-M
             Archaea; Nanoarchaeota; Nanoarchaeum.
 REFERENCE   1  (bases 1 to 490885)
   AUTHORS   Waters,E., Hohn,M.J., Ahel,I., Graham,D.E., Adams,M.D.,
             Barnstead,M., Beeson,K.Y., Bibbs,L., Bolanos,R., Keller,M.,
             Kretz,K., Lin,X., Mathur,E., Ni,J., Podar,M., Richardson,T.,
             Sutton,G.G., Simon,M., Soll,D., Stetter,K.O., Short,J.M. and
             Noordewier,M.
   TITLE     The genome of Nanoarchaeum equitans: insights into early archaeal
             evolution and derived parasitism
   JOURNAL   Proc. Natl. Acad. Sci. U.S.A. 100 (22), 12984-12988 (2003)
    PUBMED   14566062
 REFERENCE   2  (bases 1 to 490885)
   CONSRTM   NCBI Genome Project
   TITLE     Direct Submission
   JOURNAL   Submitted (17-NOV-2003) National Center for Biotechnology
             Information, NIH, Bethesda, MD 20894, USA
 REFERENCE   3  (bases 1 to 490885)
   CONSRTM   NCBI Microbial Genomes Annotation Project
   TITLE     Direct Submission
   JOURNAL   Submitted (25-JUN-2001) National Center for Biotechnology
             Information, NIH, Bethesda, MD 20894, USA
 COMMENT     PROVISIONAL REFSEQ: This record has not yet been subject to final
             NCBI review. The reference sequence was derived from AE017199.
             COMPLETENESS: full length.
 FEATURES             Location/Qualifiers
      source          1..490885
                      /organism="Nanoarchaeum equitans Kin4-M"
                      /mol_type="genomic DNA"
                      /strain="Kin4-M"
                      /db_xref="taxon:228908"
 gene            complement(486423..486962)
                 /locus_tag="NEQ550"
                 /db_xref="GeneID:2732580"
 CDS             complement(486423..486962)
                 /locus_tag="NEQ550"
                 /codon_start=1
                 /transl_table=11
                 /product="hypothetical protein"
                 /protein_id="NP_963830.1"
                 /db_xref="GI:41615332"
                 /db_xref="GeneID:2732580"
                 /translation="MLELLAGFKQSILYVLAQFKKPEYATSYTIKLVNPFYYISDSLN
                 VITSTKEDKVNYKVSLSDIAFDFPFKFPIVAIVEGKANREFTFIIDRQNKKLSYDLKK
                 GIIYIQDATIIPNGIKITVNGLAELKNIKINPNDPSITVQKVVGEQNTYIIKTSKDSV
                 KITISADFVVKAEKWLFIQ"
 promoter        486983..486988
                 /note="archaeal RNA pol III promoter consensus box Aaaaaaa
                 motif"
 misc_feature    487009..487022
                 /locus_tag="NEQ_t33"
                 /note="reverse complementary sequence cleaved during
                 processing of trans-spliced tRNAs"
ORIGIN
    1 tctcgcagag ttcttttttg tattaacaaa cccaaaaccc atagaattta atgaacccaa
   61 accgcaatcg tacaaaaatt tgtaaaattc tctttcttct ttgtctaatt ttctataaac
  121 atttaactct ttccataatg tgcctatata tactgcttcc cctctgttaa ttcttattct
  */